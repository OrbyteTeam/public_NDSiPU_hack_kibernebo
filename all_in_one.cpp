// Сборка
// g++ -O3 -fopenmp .\all_in_one_v2.cpp -o decoder 

#include <iostream>
#include <vector>
#include <fstream>
#include <algorithm>
#include <cmath>
#include <chrono>
#include <omp.h>

const double PI = 3.1415926535897;

const double Fs = 20000000.0;
const double LINE_FREQ = 15625.0;
const int SAMPLES_PER_LINE = static_cast<int>(Fs / LINE_FREQ);

int main() {
    // загрузка данных
    std::ifstream file("iq_capture.cf32", std::ios::binary);
    if (!file) return -1;

    file.seekg(0, std::ios::end);
    size_t fileSize = file.tellg();
    size_t num_samples = fileSize / sizeof(float);
    file.seekg(0, std::ios::beg);

    std::vector<float> raw_data(num_samples);
    file.read(reinterpret_cast<char*>(raw_data.data()), fileSize);
    
    auto start_time = std::chrono::high_resolution_clock::now(); // фиксируем timestamp в микросекундах

    size_t num_iq = num_samples / 2;
    std::vector<float> video_signal(num_iq - 1);

    // FM-демодуляция
    // используем OpenMP для распределения нагрузки по ядрам
    // даёт очень большое ускорение
    #pragma omp parallel for
    for (long i = 0; i < (long)(num_iq - 1); ++i) {
        float re0 = raw_data[2*i];
        float im0 = raw_data[2*i+1];
        float re1 = raw_data[2*i+2];
        float im1 = raw_data[2*i+3];

        // Re = re1*re0 + im1*im0
        // Im = im1*re0 - re1*im0
        float dot = re1 * re0 + im1 * im0; // Тут получается Re искомого произведения
        float cross = im1 * re0 - re1 * im0; // Тут получается Im искомого произведения

        video_signal[i] = std::atan2(cross, dot) * Fs / (2 * PI);
    }


    const int TAPS = 71; // Больше тапов = круче срез
    std::vector<float> kernel(TAPS);
    float fc = 5200000.0f / Fs;
    float sum_k = 0;

    for (int i = 0; i < TAPS; ++i) {
        int n = i - TAPS / 2;
        if (n == 0) kernel[i] = 2.0f * fc;
        else kernel[i] = std::sin(2.0f * PI * fc * n) / (PI * n);
        // Окно Хэмминга
        kernel[i] *= (0.54f - 0.46f * std::cos(2.0f * PI * i / (TAPS - 1)));
        sum_k += kernel[i];
    }
    for (float &k : kernel) k /= sum_k;

    std::vector<float> filtered_signal(video_signal.size(), 0.0f);

    #pragma omp parallel for
    for (long i = TAPS; i < (long)(video_signal.size() - TAPS); ++i) {
        float acc = 0;
        for (int j = 0; j < TAPS; ++j) {
            acc += video_signal[i - TAPS / 2 + j] * kernel[j];
        }
        filtered_signal[i] = acc;
    }
    video_signal = std::move(filtered_signal);



    // DC-фильтр
    double global_sum = 0;
    #pragma omp parallel for reduction(+:global_sum)
    for (long i = 0; i < (long)video_signal.size(); ++i) {
        global_sum += video_signal[i];
    }
    float mean = static_cast<float>(global_sum / video_signal.size());

    #pragma omp parallel for
    for (long i = 0; i < (long)video_signal.size(); ++i) {
        video_signal[i] -= mean;
    }

    // нормализация
    std::vector<float> sorted_data = video_signal;
    size_t n = sorted_data.size();
    
    // Ищем только 2 нужных значения, а не сортируем всё
    auto it_sync = sorted_data.begin() + static_cast<size_t>(0.01 * n); // 1 процентиль
    auto it_white = sorted_data.begin() + static_cast<size_t>(0.995 * n); // 99,5 процентиль
    std::nth_element(sorted_data.begin(), it_sync, sorted_data.end());
    float sync_level = *it_sync;
    std::nth_element(sorted_data.begin(), it_white, sorted_data.end());
    float white_level = *it_white;

    float range_inv = 1.1f / (white_level - sync_level);

    // Перегоняем все даныне в нужный диапазон, параллельно
    #pragma omp parallel for
    for (long i = 0; i < (long)video_signal.size(); ++i) {
        float s = (video_signal[i] - sync_level) * range_inv - 0.3f;
        video_signal[i] = std::clamp(s, -0.4f, 1.0f);
    }

    // Поиск HSYNC
    const float HSYNC_THRESHOLD = -0.22f; // Порог, после которого считаем что потенциально начался HSYNC
    const float MIN_HSYNC_DEPTH = -0.27f; // Порог, после чего точно увреенны что был HSYNC
    const int window = static_cast<int>(Fs * 5e-6); // окно в 5мс
    const int min_dist = static_cast<int>(SAMPLES_PER_LINE * 0.6); // HSYNC должны быть не чаще чем 60% длины строки
    
    std::vector<int> hsync_pos;
    hsync_pos.reserve(num_iq / SAMPLES_PER_LINE); // Заранее резервируем место
    
    int prev_sync = -min_dist * 2;

    for (int i = 1; i < (int)video_signal.size() - window; ++i) {
        if (video_signal[i-1] > HSYNC_THRESHOLD && video_signal[i] <= HSYNC_THRESHOLD) { // Момент падения сверху вниз (фронт)
            float min_val = video_signal[i];
            int min_idx = i;
            for(int j = i + 1; j < i + window; ++j) { // Ищем внутри окна 5мс минимальное значение
                if(video_signal[j] < min_val) {
                    min_val = video_signal[j];
                    min_idx = j;
                }
            }
            
            if (min_val < MIN_HSYNC_DEPTH && (min_idx - prev_sync) > min_dist) { // Если найденно значение меньше -0.27 и мы отошли достаточно от предыдущего hsync (60% строки), то запоминаем
                hsync_pos.push_back(min_idx);
                prev_sync = min_idx;
                i = min_idx + min_dist; // Пропускаем часть строки
            }
        }
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);

    std::cout << "HSYNCs: " << hsync_pos.size() << " | Time: " << duration.count() << " ms" << std::endl;

    // Сохранение отфильтрованного сигнала float32
    std::ofstream out_sig("filtered_signal.bin", std::ios::binary);
    if (out_sig) {
        out_sig.write(reinterpret_cast<const char*>(video_signal.data()), 
                    video_signal.size() * sizeof(float));
        out_sig.close();
        std::cout << "saved filtered_signal.bin" << std::endl;
    }

    // Сохранение позиций HSYNC int32
    std::ofstream out_sync("hsync_pos.bin", std::ios::binary);
    if (out_sync) {
        std::vector<int32_t> sync_to_save(hsync_pos.begin(), hsync_pos.end()); // !!!Сохраняем как int32_t для совместимости с numpy
        out_sync.write(reinterpret_cast<const char*>(sync_to_save.data()), 
                    sync_to_save.size() * sizeof(int32_t));
        out_sync.close();
        std::cout << "saved hsync_pos.bin" << std::endl;
    }

    return 0;
}
