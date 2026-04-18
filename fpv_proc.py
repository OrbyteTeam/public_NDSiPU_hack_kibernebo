import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QCheckBox, QDoubleSpinBox, QSpinBox, QLabel, QPushButton,
                             QScrollArea, QGridLayout)
from PyQt5.QtCore import Qt
from scipy import signal as sig


class SyncDetector:
    def __init__(self, Fs=20_000_000):
        self.Fs = Fs
        self.line_samples = int(Fs / 15625)
        self.hsync_threshold = -0.22
        self.min_hsync_depth = -0.27

    def find_hsync(self, signal):
        below = signal < self.hsync_threshold
        edges = np.where(np.diff(below.astype(int)) > 0)[0]
        hsync_pos = []
        prev = -self.line_samples * 2
        for start in edges:
            end = min(start + int(self.Fs * 12e-6), len(signal))
            segment = signal[start:end]
            min_idx = start + np.argmin(segment)
            if signal[min_idx] < self.min_hsync_depth and (start - prev) > self.line_samples * 0.6:
                hsync_pos.append(min_idx)
                prev = min_idx
        return np.array(hsync_pos)

    def find_vsync(self, hsync_pos):
        if len(hsync_pos) < 30:
            return np.array([])
        diffs = np.diff(hsync_pos)
        vsync_pos = []
        for i in range(len(diffs)):
            if diffs[i] > self.line_samples * 2.3:   # длинная пауза
                if i + 8 < len(diffs) and np.median(diffs[i+1:i+8]) < self.line_samples * 1.4:
                    vsync_pos.append(hsync_pos[i])
        return np.array(vsync_pos)


class FPVProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FPV Signal Processor — Интерактивный анализ")
        self.resize(1700, 950)

        self.Fs = 20_000_000
        self.signal_raw = np.fromfile('composite_video.raw', dtype=np.float32)
        self.detector = SyncDetector(self.Fs)
        self.hsync = None
        self.vsync = None

        self.init_ui()
        self.update_all()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # === Панель управления ===
        ctrl_layout = QVBoxLayout()
        ctrl_layout.setSpacing(12)

        self.cb_dc = QCheckBox("DC Removal")
        self.cb_dc.setChecked(True)

        self.cb_notch = QCheckBox("Notch Filter (4.43 МГц)")
        self.cb_notch.setChecked(True)
        self.spin_q = QDoubleSpinBox()
        self.spin_q.setRange(5, 50)
        self.spin_q.setValue(20)
        self.spin_q.setSingleStep(1)

        self.cb_lp = QCheckBox("Low-Pass Filter")
        self.cb_lp.setChecked(True)
        self.spin_cutoff = QDoubleSpinBox()
        self.spin_cutoff.setRange(4.0, 9.0)
        self.spin_cutoff.setValue(6.0)
        self.spin_cutoff.setSingleStep(0.1)

        self.cb_norm = QCheckBox("Нормализация")
        self.cb_norm.setChecked(True)
        self.spin_offset = QSpinBox()
        self.spin_offset.setRange(50, 400)
        self.spin_offset.setValue(180)
        self.spin_offset.setSingleStep(10)

        for w in [self.cb_dc, self.cb_notch, self.cb_lp, self.cb_norm]:
            w.stateChanged.connect(self.update_all)
        for w in [self.spin_q, self.spin_cutoff, self.spin_offset]:
            w.valueChanged.connect(self.update_all)

        # Группы
        for title, widgets in [
            ("DC Removal", [self.cb_dc]),
            ("Notch Filter", [self.cb_notch, QLabel("Q:"), self.spin_q]),
            ("Low-Pass Filter", [self.cb_lp, QLabel("Cutoff (МГц):"), self.spin_cutoff]),
            ("Нормализация и Offset", [self.cb_norm, QLabel("Line Offset:"), self.spin_offset]),
        ]:
            gb = QGroupBox(title)
            lay = QVBoxLayout()
            for widget in widgets:
                lay.addWidget(widget)
            gb.setLayout(lay)
            ctrl_layout.addWidget(gb)

        ctrl_layout.addStretch()
        btn = QPushButton("Обновить всё")
        btn.clicked.connect(self.update_all)
        ctrl_layout.addWidget(btn)

        ctrl_widget = QWidget()
        ctrl_widget.setLayout(ctrl_layout)
        main_layout.addWidget(ctrl_widget, 1)

        # === Графики и кадры ===
        right_layout = QVBoxLayout()

        self.fig1, self.ax1 = plt.subplots(figsize=(10, 3))   # 150 мкс
        self.canvas1 = FigureCanvas(self.fig1)
        right_layout.addWidget(self.canvas1)

        self.fig2, self.ax2 = plt.subplots(figsize=(10, 3))   # 5 мс
        self.canvas2 = FigureCanvas(self.fig2)
        right_layout.addWidget(self.canvas2)

        self.fig3, self.ax3 = plt.subplots(figsize=(10, 3))   # Спектр
        self.canvas3 = FigureCanvas(self.fig3)
        right_layout.addWidget(self.canvas3)

        # === Два крупных кадра ===
        self.frame_layout = QHBoxLayout()
        self.frame_widget = QWidget()
        self.frame_widget.setLayout(self.frame_layout)
        right_layout.addWidget(self.frame_widget, 2)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 4)

    def process_signal(self):
        x = self.signal_raw.copy()
        if self.cb_dc.isChecked():
            x -= np.mean(x)
        if self.cb_notch.isChecked():
            b, a = sig.iirnotch(4.43e6 / (self.Fs/2), self.spin_q.value())
            x = sig.filtfilt(b, a, x)
        if self.cb_lp.isChecked():
            b, a = sig.butter(8, self.spin_cutoff.value()*1e6/(self.Fs/2), btype='low')
            x = sig.filtfilt(b, a, x)
        if self.cb_norm.isChecked():
            x -= np.mean(x)
            p1, p99 = np.percentile(x, [1, 99])
            x = (x - p1) / (p99 - p1 + 1e-8)
            x = x * 1.05 - 0.32
            x = np.clip(x, -0.4, 1.0)
        return x

    def update_all(self):
        self.signal = self.process_signal()
        self.hsync = self.detector.find_hsync(self.signal)
        self.vsync = self.detector.find_vsync(self.hsync)

        self.update_oscillograms()
        self.update_spectrum()
        self.update_frames()

    def update_oscillograms(self):
        self.ax1.clear()
        self.ax2.clear()

        # 150 мкс
        n1 = int(0.00015 * self.Fs)
        t1 = np.arange(n1) / self.Fs * 1e6
        self.ax1.plot(t1, self.signal[:n1], 'b', lw=0.8)
        self.plot_markers(self.ax1, t1, n1)
        self.ax1.set_title('Осциллограмма — 150 мкс')
        self.ax1.grid(True, alpha=0.5)

        # 5 мс
        n2 = int(0.005 * self.Fs)
        t2 = np.arange(n2) / self.Fs * 1000
        self.ax2.plot(t2, self.signal[:n2], 'b', lw=0.6)
        self.plot_markers(self.ax2, t2, n2, ms_scale=1000)
        self.ax2.set_title('Осциллограмма — 5 мс')
        self.ax2.grid(True, alpha=0.5)

        self.canvas1.draw()
        self.canvas2.draw()

    def plot_markers(self, ax, t, max_samples, ms_scale=1e6):
        # HSYNC
        h_mask = self.hsync < max_samples
        if np.any(h_mask):
            ax.plot(t[self.hsync[h_mask]], self.signal[self.hsync[h_mask]], 
                   'r^', markersize=7, label='HSYNC')

        # VSYNC
        if self.vsync is not None and len(self.vsync) > 0:
            v_mask = self.vsync < max_samples
            if np.any(v_mask):
                ax.plot(t[self.vsync[v_mask]], self.signal[self.vsync[v_mask]], 
                       'g*', markersize=12, label='VSYNC')

        ax.legend()

    def update_spectrum(self):
        self.ax3.clear()
        f, pxx = sig.welch(self.signal, fs=self.Fs, nperseg=65536, scaling='density')
        self.ax3.semilogy(f/1e6, pxx, 'r', lw=1)
        self.ax3.set_title('Спектр сигнала')
        self.ax3.axvline(4.43, color='green', ls='--', alpha=0.7, label='4.43 МГц')
        self.ax3.axvline(self.spin_cutoff.value(), color='orange', ls='--', alpha=0.7)
        self.ax3.grid(True, alpha=0.5)
        self.ax3.legend()
        self.canvas3.draw()

    def update_frames(self):
        # Очистка предыдущих кадров
        for i in reversed(range(self.frame_layout.count())):
            self.frame_layout.itemAt(i).widget().deleteLater()

        extractor = VideoFrameExtractor(self.Fs)
        extractor.line_offset = self.spin_offset.value()
        lines = extractor.extract_lines(self.signal, self.hsync)

        for i in range(2):  # Только 2 крупных кадра
            if (i+1)*625 > len(lines):
                break
            frame = extractor.form_frame(lines[i*625:(i+1)*625])
            if frame is not None:
                fig, ax = plt.subplots(figsize=(7, 5.5))
                ax.imshow(frame, cmap='gray')
                ax.set_title(f'Кадр {i+1}')
                ax.axis('off')
                canvas = FigureCanvas(fig)
                self.frame_layout.addWidget(canvas)


class VideoFrameExtractor:
    def __init__(self, Fs):
        self.Fs = Fs
        self.samples_per_line = 1280
        self.line_offset = 180

    def extract_lines(self, signal, hsync_pos):
        lines = []
        for pos in hsync_pos:
            start = pos + self.line_offset
            end = start + self.samples_per_line
            if end < len(signal):
                lines.append(signal[start:end])
        return np.array(lines)

    def form_frame(self, lines):
        if len(lines) < 500: 
            return None
        frame = lines[:576]
        frame = (frame - frame.min()) / (frame.max() - frame.min() + 1e-8) * 255
        return np.clip(frame, 0, 255).astype(np.uint8)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FPVProcessor()
    window.show()
    sys.exit(app.exec_())