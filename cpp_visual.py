import numpy as np
import matplotlib.pyplot as plt


Fs = 20_000_000.0

# Читаем сигнал
signal = np.fromfile('filtered_signal.bin', dtype=np.float32)

# позиции синхроимпульсов
hsync_pos = np.fromfile('hsync_pos.bin', dtype=np.int32)

print(f"Загружен сигнал: {len(signal)} отсчетов")
print(f"Загружено HSYNC: {len(hsync_pos)}")

import plotter
plotter.oscil(signal, 20e6, 800)
plotter.spectre(signal, 20e6)

target_width = 1280
frame = []

for i in range(len(hsync_pos) - 1):
    start = hsync_pos[i]
    end = hsync_pos[i+1]
    line = signal[start:end]
    
    # Ресайзим строку до фиксированной ширины 
    if len(line) > 100: # если это строка нормальной длины
        line_resized = np.interp(
            np.linspace(0, len(line), target_width), 
            np.arange(len(line)), 
            line
        )
        frame.append(line_resized)

plt.figure(figsize=(10, 8))
plt.imshow(np.array(frame)[:300], cmap='gray', aspect='auto')
plt.show()
