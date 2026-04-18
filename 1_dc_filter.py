import numpy as np
import matplotlib.pyplot as plt
from scipy import signal as sig
import plotter

video_signal = np.fromfile('composite_video.raw', dtype=np.float32)
Fs = 20_000_000.0

print(f"Загружено {len(video_signal):,} отсчётов")


# Убираем постоянную составляющую (DC offset)
mean_value = np.mean(video_signal)
filtered = video_signal - mean_value
print(f"DC-смещение удалено: {mean_value:.2f}")
filtered.astype(np.float32).tofile('1_filtered_video.raw') # сохранение в файл

# визуализация
plotter.oscil(filtered, Fs, len(filtered))
plotter.oscil(filtered, Fs, int(0.00015 * Fs))
plotter.spectre(filtered, Fs)