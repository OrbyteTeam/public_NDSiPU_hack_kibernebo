import numpy as np
import plotter

video_signal = np.fromfile('4_filtered_video.raw', dtype=np.float32)
Fs = 20_000_000.0

print(f"Загружено {len(video_signal):,} отсчётов")


# Находим уровень синхроимпульсов (самые низкие значения)
sync_level = np.percentile(video_signal, 1.0)  # нижний 1%
white_level = np.percentile(video_signal, 99.5)

# Приводим к стандартным уровням композитного видео
filtered = (video_signal - sync_level) / (white_level - sync_level)
filtered = filtered * 1.1 - 0.3

filtered = np.clip(filtered, -0.4, 1.0)

filtered.astype(np.float32).tofile('5_normalized_video.raw')

# визуализация
plotter.oscil(filtered, Fs, len(filtered))
plotter.oscil(filtered, Fs, int(0.00015 * Fs))
plotter.spectre(filtered, Fs)