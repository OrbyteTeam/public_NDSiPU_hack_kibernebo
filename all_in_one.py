import numpy as np
from scipy import signal as sig
import matplotlib.pyplot as plt
import time

# Загрузка IQ данных из файла .cf32
data = np.fromfile('iq_capture.cf32', dtype=np.float32)
start_time = time.time_ns()
iq = data[0::2] + 1j * data[1::2] # Собираем комплексное число

# Удаление постоянной составляющей (DC offset)
iq = iq - np.mean(iq)

# FM-демодуляция, извлечение композитного видеосигнала
demod = np.angle(iq[1:] * np.conj(iq[:-1]))

# Перевод в физические единицы (Гц)
Fs = 20_000_000.0
video_signal = demod * (Fs / (2 * np.pi))

print(f"Демодулировано. Получен сигнал длиной {len(video_signal)} отсчётов")


# DC filter
mean_value = np.mean(video_signal)
filtered = video_signal - mean_value

# Notch-фильтр на 4.43 МГц (убираем цветовую поднесущую PAL)
notch_freq = 4.43e6
quality_factor = 20
b_notch, a_notch = sig.iirnotch(notch_freq / (Fs / 2), quality_factor)
filtered = sig.filtfilt(b_notch, a_notch, filtered)

# Low-Pass Filter - убираем высокие частоты и большую часть "игл"
cutoff = 2.4e6
order = 8
b_lp, a_lp = sig.butter(order, cutoff / (Fs / 2), btype='low')
filtered = sig.filtfilt(b_lp, a_lp, filtered)

# DC filter
mean_value = np.mean(filtered)
filtered = filtered - mean_value

# Находим уровень синхроимпульсов (самые низкие значения)
sync_level = np.percentile(filtered, 1.0)        # нижний 1%
white_level = np.percentile(filtered, 99.5)

# Приводим к стандартным уровням композитного видео
filtered = (filtered - sync_level) / (white_level - sync_level)
filtered = filtered * 1.1 - 0.3                         # sync ≈ -0.3, white ≈ 0.8

filtered = np.clip(filtered, -0.4, 1.0)



HSYNC_THRESHOLD = -0.22
MIN_HSYNC_DEPTH = -0.27
LINE_SAMPLES = int(Fs / 15625.0)
# hsync
below = filtered < HSYNC_THRESHOLD
edges = np.where(np.diff(below.astype(int)) > 0)[0]

hsync_pos = []
prev = -LINE_SAMPLES * 2

for start in edges:
    end = min(start + int(Fs * 12e-6), len(filtered))
    segment = filtered[start:end]
    min_idx = start + np.argmin(segment)
    min_val = filtered[min_idx]
    
    if min_val < MIN_HSYNC_DEPTH and (start - prev) > LINE_SAMPLES * 0.6:
        hsync_pos.append(min_idx)
        prev = min_idx
        
hsync_pos = np.array(hsync_pos)
end_time = time.time_ns()
print(f"Найдено HSYNC: {len(hsync_pos)} за {(end_time-start_time)/1_000_000} мс")
# 10 млн отсчетов (500мс записи) парсятся примерно за 1276-1500 мс  


# визуализация
MAX_MS = 50.0
max_samples = int(MAX_MS * Fs / 1000)

t = np.arange(max_samples) / Fs * 1000  # время в миллисекундах

plt.figure(figsize=(15, 7))
plt.plot(t, filtered[:max_samples], 'b-', linewidth=0.7, label='Сигнал')

# Отображаем только те HSYNC, которые попадают в видимый диапазон
mask_h = hsync_pos < max_samples
plt.plot(t[hsync_pos[mask_h]], filtered[hsync_pos[mask_h]], 
        'r^', markersize=6, label='HSYNC')

plt.axhline(y=HSYNC_THRESHOLD, color='red', linestyle='--', 
            alpha=0.7, label='Порог HSYNC')
plt.title(f'Детекция HSYNC и VSYNC (первые {MAX_MS} мс)')
plt.xlabel('Время, мс')
plt.ylabel('Нормализованная амплитуда')
plt.grid(True, alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()


samples_per_line = int(Fs / 15625)   # 1280 при 20 Msps

lines = []
for i in range(len(hsync_pos) - 1):
    start = hsync_pos[i]
    end = start + samples_per_line
    if end < len(filtered):
        line = filtered[start:end]
        lines.append(line)
lines = np.array(lines)




# Берём первые lines_per_frame строк
# lines_per_frame=625
# frame = lines[:lines_per_frame]
frame = lines[:]

# Нормализуем для изображения (0..255)
frame = (frame - frame.min()) / (frame.max() - frame.min()) * 255
frame = np.clip(frame, 0, 255).astype(np.uint8)


plt.figure(figsize=(10, 8))
plt.imshow(frame, cmap='gray', aspect='auto')
plt.title("Кадр")
plt.axis('off')
plt.tight_layout()
plt.show()