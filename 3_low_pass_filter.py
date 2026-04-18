import numpy as np
import matplotlib.pyplot as plt
from scipy import signal as sig
import plotter

video_signal = np.fromfile('2_filtered_video.raw', dtype=np.float32)
Fs = 20_000_000.0

print(f"Загружено {len(video_signal):,} отсчётов")


# Low-Pass Filter
cutoff = 2_400_000
order = 8
b_lp, a_lp = sig.butter(order, cutoff / (Fs / 2), btype='low')
filtered = sig.filtfilt(b_lp, a_lp, video_signal)

filtered.astype(np.float32).tofile('3_filtered_video.raw')


# визуализация
plotter.oscil(filtered, Fs, len(filtered))
plotter.oscil(filtered, Fs, int(0.00015 * Fs))
plotter.spectre(filtered, Fs)