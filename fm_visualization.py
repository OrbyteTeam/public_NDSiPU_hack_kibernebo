import matplotlib.pyplot as plt
import numpy as np
from scipy import signal as sig

video_signal = np.fromfile('composite_video.raw', dtype=np.float32)

Fs = 20_000_000.0
duration = len(video_signal) / Fs

print(f"Длительность сигнала: {duration:.3f} сек ({len(video_signal):,} отсчётов)")

plt.figure(figsize=(12, 5))

# Визуализация сигнала
samples_to_show = int(0.00015 * Fs)          # 5 миллисекунд (примерно 3 строки PAL)
# samples_to_show = len(video_signal)
t = np.arange(samples_to_show) / Fs * 1000  # в миллисекундах

plt.plot(t, video_signal[:samples_to_show], linewidth=0.8, color='blue')
plt.title('Демодулированный композитный видеосигнал (150 мкс)')
plt.xlabel('Время, мкс')
plt.ylabel('Амплитуда (отклонение частоты, Гц)')
plt.grid(True, alpha=0.5)

# Добавляем ориентировочные уровни
plt.axhline(y=0, color='black', linestyle='--', alpha=1, label='Нулевой уровень')
plt.legend()
plt.tight_layout()
plt.show()


# Спектр
# f, pxx = sig.welch(video_signal, fs=Fs, nperseg=65536, scaling='density', average='median')
# plt.semilogy(f/1e6, pxx, color='red', linewidth=1)
# plt.title('Спектр демодулированного композитного видеосигнала')
# plt.xlabel('Частота, МГц')
# plt.ylabel('Мощность / частота (log)')
# plt.grid(True, alpha=0.5)

# # Отмечаем важные частоты
# plt.axvline(x=4.43, color='green', linestyle='--', alpha=0.7, label='4.43 МГц — цветовая поднесущая PAL')
# plt.axvline(x=5.5, color='orange', linestyle='--', alpha=0.6, label='Примерная граница яркости')
# plt.legend()
# plt.tight_layout()
# plt.show()