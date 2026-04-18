import numpy as np
import plotter

# Загрузка IQ данных из файла .cf32
data = np.fromfile('iq_capture.cf32', dtype=np.float32)
iq = data[0::2] + 1j * data[1::2] # Собираем комплексное число

# Удаление постоянной составляющей (DC offset)
iq = iq - np.mean(iq)

# FM-демодуляция
demod = np.angle(iq[1:] * np.conj(iq[:-1]))

# Перевод в физические единицы (Гц)
Fs = 20_000_000.0
video_signal = demod * (Fs / (2 * np.pi))

# Сохранение сырого вещественного сигнала
video_signal.astype(np.float32).tofile('composite_video.raw')

print(f" сигнал длиной {len(video_signal)} отсчётов")

plotter.oscil(video_signal, Fs, len(video_signal))

plotter.oscil(video_signal, Fs, int(0.00015 * Fs))

plotter.spectre(video_signal, Fs)
