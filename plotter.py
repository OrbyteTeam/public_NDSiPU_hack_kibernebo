import numpy as np
import matplotlib.pyplot as plt
from scipy import signal as sig


def oscil(signal, Fs, samples_to_show):
    plt.figure(figsize=(12, 5))

    t = np.arange(samples_to_show) / Fs * 1000  # в миллисекундах

    plt.plot(t, signal[:samples_to_show], linewidth=0.8, color='blue')
    plt.title('Демодулированный композитный видеосигнал')
    plt.xlabel('Время')
    plt.ylabel('Амплитуда (отклонение частоты, Гц)')
    plt.grid(True, alpha=0.5)

    plt.axhline(y=0, color='black', linestyle='--', alpha=1, label='Нулевой уровень')
    plt.legend()
    plt.tight_layout()
    plt.show()

def spectre(signal, Fs):
    f, pxx = sig.welch(signal, fs=Fs, nperseg=65536, scaling='density', average='median')
    plt.semilogy(f/1_000_000, pxx, color='red', linewidth=1)
    plt.title('Спектр демодулированного композитного видеосигнала')
    plt.xlabel('Частота, МГц')
    plt.ylabel('Мощность / частота (log)')
    plt.grid(True, alpha=0.5)

    # важные частоты
    plt.axvline(x=4.43, color='green', linestyle='--', alpha=0.7, label='4.43 МГц - цветовая поднесущая PAL')
    plt.axvline(x=5.5, color='orange', linestyle='--', alpha=0.6, label='Примерная граница яркости')
    plt.legend()
    plt.tight_layout()
    plt.show()