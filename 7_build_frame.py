import numpy as np
import matplotlib.pyplot as plt
from scipy import signal as sig
import plotter

filtered = np.fromfile('5_normalized_video.raw', dtype=np.float32)
hsync_pos = np.fromfile('hsync.raw', dtype=np.int32)
Fs = 20_000_000.0

samples_per_line = int(Fs / 15625)   # 1280 при 20 Msps
lines_per_field = 312                # Примерно для PAL (можно 312 или 313)

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
frame = lines[:]  # клеим все кадры в один большой кадр

# Нормализуем для изображения (0..255)
frame = (frame - frame.min()) / (frame.max() - frame.min()) * 255
frame = np.clip(frame, 0, 255).astype(np.uint8)


plt.figure(figsize=(10, 8))
plt.imshow(frame, cmap='gray', aspect='auto')
plt.title("Кадр")
plt.axis('off')
plt.tight_layout()
plt.show()