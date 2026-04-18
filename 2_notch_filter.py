import numpy as np
import matplotlib.pyplot as plt
from scipy import signal as sig
import plotter

video_signal = np.fromfile('1_filtered_video.raw', dtype=np.float32)
Fs = 20_000_000.0

print(f"Загружено {len(video_signal):,} отсчётов")


# Notch-фильтр на 4.43 МГц (убираем цветовую поднесущую PAL)
notch_freq = 4_430_000
quality_factor = 20
b_notch, a_notch = sig.iirnotch(notch_freq / (Fs / 2), quality_factor)
filtered = sig.filtfilt(b_notch, a_notch, video_signal)

filtered.astype(np.float32).tofile('2_filtered_video.raw')

# визуализация
plotter.oscil(filtered, Fs, len(filtered))
plotter.oscil(filtered, Fs, int(0.00015 * Fs))
plotter.spectre(filtered, Fs)