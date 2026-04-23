import numpy as np
import matplotlib.pyplot as plt
from scipy import signal as sig
import plotter
Fs = 20e6

raw = np.fromfile('composite_video.raw', dtype=np.float32)
plotter.oscil(raw, Fs=Fs, samples_to_show=int(Fs*0.001))
plotter.spectre(raw, Fs)

cutoff = 3.0e6
order = 2
b_lp, a_lp = sig.butter(order, cutoff / (Fs / 2), btype='low')
filtered = sig.filtfilt(b_lp, a_lp, raw)

notch_freq = 4_430_000
quality_factor = 20
b_notch, a_notch = sig.iirnotch(notch_freq / (Fs / 2), quality_factor)
filtered = sig.filtfilt(b_notch, a_notch, filtered)

sync_level = np.percentile(filtered, 1.0)
white_level = np.percentile(filtered, 99.5)

filtered = (filtered - sync_level) / (white_level - sync_level)
filtered = filtered * 1.1 - 0.3

filtered = np.clip(filtered, -0.4, 1.0)


plotter.oscil(filtered, Fs=Fs, samples_to_show=int(Fs*0.001))
plotter.spectre(filtered, Fs)


fs = 20e6
samples_per_line = int(64e-6 * fs)  
threshold = -0.22

sync_indices = np.where((filtered[:-1] > threshold) & (filtered[1:] <= threshold))[0]
from scipy.interpolate import interp1d

sync_indices = np.where((filtered[:-1] > threshold) & (filtered[1:] <= threshold))[0]

width_px = 1200 
num_lines = len(sync_indices) - 1
canvas = np.zeros((num_lines, width_px))

print(f"Склеиваем {num_lines} строк")

for i in range(num_lines):
    start = sync_indices[i]
    end = sync_indices[i+1]
    
    line_raw = filtered[start:end]
    
    if len(line_raw) > 100: 
        x_old = np.linspace(0, 1, len(line_raw))
        x_new = np.linspace(0, 1, width_px)
        
        f_interp = interp1d(x_old, line_raw, kind='linear')
        canvas[i, :] = f_interp(x_new)

plt.figure(figsize=(12, 30))
active_video_start = int(width_px * 0.15) 
plt.imshow(canvas[:1576, active_video_start:], cmap='gray', aspect='auto', vmin=0, vmax=0.7)
plt.title("Вертикальное полотно (выровненное)")
plt.xlabel("Пиксели (активная область)")
plt.ylabel("Номер строки")
plt.show()


start_line = 130 
frame_raw = canvas[start_line : start_line + 600, active_video_start:]


field1 = frame_raw[0::2, :] 
field2 = frame_raw[1::2, :] 


plt.figure(figsize=(10, 10))

plt.imshow(field1, cmap='gray', aspect=2.0, vmin=0.1, vmax=0.6) 

plt.title("Финальный декодированный кадр (Field 1)")
plt.axis('off')
plt.show()


clean_frame = canvas[810:1100, active_video_start:-50] 

plt.figure(figsize=(12, 9))

plt.imshow(clean_frame, cmap='gray', aspect=2.0, vmin=0.1, vmax=0.6)

plt.title("Декодированный кадр")
plt.axis('off')
plt.show()
single_field = canvas[850:1130, active_video_start:-50] 
plt.figure(figsize=(10, 7))
plt.imshow(single_field, cmap='gray', aspect=2.0, vmin=0.1, vmax=0.6)
plt.show()