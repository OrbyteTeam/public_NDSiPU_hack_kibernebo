import numpy as np
import plotter
import matplotlib.pyplot as plt

filtered = np.fromfile('5_normalized_video.raw', dtype=np.float32)
Fs = 20_000_000.0

print(f"Загружено {len(filtered):,} отсчётов")


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
hsync_pos.astype(np.int32).tofile('hsync.raw')

print(f"Найдено HSYNC: {len(hsync_pos)}")


# визуализация
MAX_MS = 5.0
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
plt.title(f'Детекция HSYNC (первые {MAX_MS} мс)')
plt.xlabel('Время, мс')
plt.ylabel('Нормализованная амплитуда')
plt.grid(True, alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()