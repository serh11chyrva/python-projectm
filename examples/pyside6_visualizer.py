"""An interactive Qt visualizer with direct GPU and background NumPy modes."""

import queue
import sys
import time
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QTimer, Slot
from PySide6.QtGui import QAction, QImage, QKeySequence, QSurfaceFormat
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSlider, QVBoxLayout, QWidget,
)

from python_projectm.integrations.pyside6 import (
    FrameEmitter, NumpyViewport, ProjectMWidget, RenderThread,
)
from python_projectm.integrations.pyside6.context import opengl_format

from ._common import AudioSource, DEMO_PRESET, OUTPUT_DIR, audio_frame_count, parser


STYLE = """
QMainWindow, QWidget#studio { background: #0b101a; color: #e7edf7; }
QLabel { color: #e7edf7; }
QLabel#eyebrow { color: #68dec4; font-size: 11px; font-weight: 600; }
QLabel#heading { font-size: 25px; font-weight: 600; }
QLabel#muted { color: #a5b2c7; }
QLabel#error { color: #ffb0a7; }
QGroupBox { color: #a5b2c7; border: 1px solid #2b3b51; border-radius: 8px;
            margin-top: 12px; padding: 18px 12px 12px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }
QPushButton { color: #e7edf7; background: #1b2a3f; border: 1px solid #354963;
              border-radius: 5px; padding: 8px 10px; }
QPushButton:hover { background: #293d57; }
QPushButton:checked { color: #081b18; background: #68dec4; }
QPushButton#primary { color: #081b18; background: #68dec4; border: 0; font-weight: 600; }
QCheckBox { color: #cbd6e7; spacing: 8px; }
QSlider::groove:horizontal { height: 4px; background: #354963; border-radius: 2px; }
QSlider::handle:horizontal { width: 14px; margin: -5px 0; border-radius: 7px; background: #68dec4; }
QStatusBar { color: #a5b2c7; background: #121c2b; }
"""


def build_parser():
    options = parser(__doc__)
    options.add_argument("--mode", choices=("gpu", "worker"), default="gpu",
                         help="Direct QOpenGLWidget or background rendering with CPU frame display")
    options.add_argument("--screenshot", type=Path, help="Save a PNG frame when --frames finishes")
    return options


class VisualizerWindow(QMainWindow):
    """Keep all GUI and PCM production on the GUI thread; queue worker commands."""

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.audio = AudioSource(args.wav)
        self.worker = None
        self._closing = False
        self._finishing = False
        self._ready = False
        self._last_frame = None
        self._audio_ticks = 0
        self._stats_time = time.monotonic()
        self._stats_frames = 0
        self._requested_size = (args.width, args.height)
        self.frame_count = 0
        self.exit_code = 0
        self.setWindowTitle("projectM Studio | PySide6")
        self.resize(args.width + 320, max(620, args.height + 110))
        self.setStyleSheet(STYLE)

        self._audio_timer = QTimer(self)
        self._audio_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._audio_timer.setInterval(20)
        self._audio_timer.timeout.connect(self._feed_audio)
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(150)
        self._resize_timer.timeout.connect(self._resize_worker)
        self._startup_timer = QTimer(self)
        self._startup_timer.setSingleShot(True)
        self._startup_timer.timeout.connect(self._startup_failed)

        central = QWidget()
        central.setObjectName("studio")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(14)
        eyebrow = QLabel("PROJECTM / PYTHON")
        eyebrow.setObjectName("eyebrow")
        layout.addWidget(eyebrow)
        heading = QLabel("Audio-reactive studio")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        body = QHBoxLayout()
        body.setSpacing(20)
        layout.addLayout(body, stretch=1)

        if args.mode == "gpu":
            self.viewport = ProjectMWidget(central, fps=args.fps)
            self.viewport.initialized.connect(self._on_ready)
            self.viewport.frameSwapped.connect(self._count_frame)
            self.viewport.error.connect(self._on_error)
        else:
            self.viewport = NumpyViewport(central, keep_aspect=True)
        self.viewport.setMinimumSize(320, 180)
        body.addWidget(self.viewport, stretch=1)
        panel = QWidget()
        panel.setFixedWidth(260)
        controls = QVBoxLayout(panel)
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(12)
        body.addWidget(panel)

        mode = QLabel("DIRECT GPU" if args.mode == "gpu" else "BACKGROUND / NUMPY")
        mode.setObjectName("eyebrow")
        controls.addWidget(mode)
        self.metrics = QLabel("Waiting for the first frame...")
        self.metrics.setObjectName("muted")
        self.metrics.setWordWrap(True)
        controls.addWidget(self.metrics)

        preset_box = QGroupBox("PRESET")
        preset_layout = QVBoxLayout(preset_box)
        self.preset_label = QLabel()
        self.preset_label.setWordWrap(True)
        preset_layout.addWidget(self.preset_label)
        open_preset = QPushButton("Open preset...")
        open_preset.setObjectName("primary")
        open_preset.clicked.connect(self.choose_preset)
        preset_layout.addWidget(open_preset)
        demo = QPushButton("Use bundled preset")
        demo.clicked.connect(lambda: self.load_preset_path(DEMO_PRESET))
        preset_layout.addWidget(demo)
        self.smooth = QCheckBox("Smooth preset transitions")
        self.smooth.setChecked(True)
        preset_layout.addWidget(self.smooth)
        controls.addWidget(preset_box)

        audio_box = QGroupBox("PCM INPUT")
        audio_layout = QVBoxLayout(audio_box)
        self.audio_label = QLabel()
        self.audio_label.setWordWrap(True)
        audio_layout.addWidget(self.audio_label)
        open_wav = QPushButton("Open WAV...")
        open_wav.clicked.connect(self.choose_wav)
        audio_layout.addWidget(open_wav)
        synthetic = QPushButton("Use synthetic stereo")
        synthetic.clicked.connect(self.use_demo_audio)
        audio_layout.addWidget(synthetic)
        self.pause_button = QPushButton("Pause PCM")
        self.pause_button.setCheckable(True)
        self.pause_button.setToolTip("Send silence while keeping the source position; animation continues")
        self.pause_button.toggled.connect(self._pause_changed)
        audio_layout.addWidget(self.pause_button)
        self.gain_label = QLabel("Input gain / 65%")
        audio_layout.addWidget(self.gain_label)
        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setRange(0, 100)
        self.gain_slider.setValue(65)
        self.gain_slider.valueChanged.connect(lambda value: self.gain_label.setText(f"Input gain / {value}%"))
        audio_layout.addWidget(self.gain_slider)
        note = QLabel("Visualization only. No audio playback or system capture.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        audio_layout.addWidget(note)
        controls.addWidget(audio_box)

        snapshot = QPushButton("Save frame...")
        snapshot.clicked.connect(self.choose_snapshot)
        controls.addWidget(snapshot)
        self.error_label = QLabel()
        self.error_label.setObjectName("error")
        self.error_label.setWordWrap(True)
        controls.addWidget(self.error_label)
        controls.addStretch()
        self.setCentralWidget(central)
        self._set_audio_label()
        self._create_actions()

        if args.mode == "worker":
            self.emitter = FrameEmitter(self)
            self.emitter.frame_ready.connect(self._on_worker_frame)
            self.emitter.error.connect(self._on_error)
            self.emitter.finished.connect(self._worker_finished)
            self.worker = RenderThread(args.width, args.height, self.emitter, fps=args.fps)
            self.viewport.installEventFilter(self)
        self.load_preset_path(args.preset, smooth=False)
        self._startup_timer.start(15000)
        if self.worker is not None:
            self.worker.start()
        QApplication.instance().aboutToQuit.connect(self.shutdown)

    def _create_actions(self):
        menu = self.menuBar().addMenu("File")
        for text, shortcut, callback in (
            ("Open preset...", "Ctrl+O", self.choose_preset),
            ("Open WAV...", "Ctrl+Shift+O", self.choose_wav),
            ("Save frame...", "Ctrl+S", self.choose_snapshot),
            ("Close", "Escape", self.close),
        ):
            action = QAction(text, self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            menu.addAction(action)
        pause = QAction("Pause PCM", self)
        pause.setShortcut(QKeySequence("Space"))
        pause.triggered.connect(self.pause_button.toggle)
        self.addAction(pause)

    @Slot()
    def _on_ready(self):
        if self._ready or self._closing:
            return
        self._ready = True
        self._startup_timer.stop()
        self._audio_timer.start()
        self.statusBar().showMessage(f"Ready / target {self.args.fps} FPS / Space pauses PCM")

    @Slot()
    def _startup_failed(self):
        self._on_error(RuntimeError("No rendered frame within 15 seconds; check the desktop OpenGL driver"))

    @Slot()
    def _feed_audio(self):
        if self._closing:
            return
        try:
            frames = audio_frame_count(self._audio_ticks, self.audio.sample_rate, 50)
            self._audio_ticks += 1
            samples = self.audio.read(frames, gain=self.gain_slider.value() / 100,
                                      paused=self.pause_button.isChecked())
            target = self.worker if self.worker is not None else self.viewport
            target.add_pcm(samples)
        except queue.Full:
            # Never block the GUI if a render worker falls behind the producer.
            self.statusBar().showMessage("Renderer busy / dropped one PCM block", 2000)
        except Exception as error:
            self._audio_timer.stop()
            self._on_error(error)

    @Slot(object)
    def _on_worker_frame(self, frame):
        if self._closing:
            return
        self._last_frame = frame
        self.viewport.set_frame(frame)
        self._on_ready()
        self._count_frame()

    @Slot()
    def _count_frame(self):
        if self._closing or self._finishing:
            return
        self.frame_count += 1
        self._stats_frames += 1
        elapsed = time.monotonic() - self._stats_time
        if elapsed >= 0.5:
            if self._last_frame is not None:
                height, width, _ = self._last_frame.shape
            else:
                ratio = self.viewport.devicePixelRatioF()
                width = int(self.viewport.width() * ratio + 0.5)
                height = int(self.viewport.height() * ratio + 0.5)
            stage = "presented" if self.args.mode == "gpu" else "received"
            self.metrics.setText(f"{width} x {height} pixels\n{self._stats_frames / elapsed:.1f} FPS {stage} / {self.frame_count} frames")
            self._stats_time = time.monotonic()
            self._stats_frames = 0
        if self.args.frames and self.frame_count >= self.args.frames:
            self._finishing = True
            # Saving outside paintGL avoids reentrant widget painting.
            QTimer.singleShot(0, self._finish)

    @Slot(object)
    def _on_error(self, error):
        print(f"PySide6: {error}", file=sys.stderr)
        if self._closing:
            self.exit_code = 1
            return
        self.error_label.setText(str(error))
        self.statusBar().showMessage("Operation failed / choose a valid input to continue")
        if self.args.frames:
            self.exit_code = 1
            QTimer.singleShot(0, self.close)

    @Slot()
    def _worker_finished(self):
        if not self._closing:
            self._audio_timer.stop()
            self._on_error(self.worker.error or RuntimeError("Render worker stopped"))

    def load_preset_path(self, path, *, smooth=None):
        self.error_label.clear()
        self.statusBar().showMessage(f"Preset requested / {Path(path).name}")
        try:
            if not Path(path).is_file():
                raise FileNotFoundError(f"Preset file not found: {path}")
            target = self.worker if self.worker is not None else self.viewport
            target.load_preset_file(path, smooth=self.smooth.isChecked() if smooth is None else smooth)
            self.preset_label.setText(Path(path).name)
            self.preset_label.setToolTip(str(path))
        except Exception as error:
            self._on_error(error)

    @Slot()
    def choose_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Milkdrop preset", str(DEMO_PRESET.parent),
                                             "Milkdrop presets (*.milk);;All files (*)")
        if path:
            self.load_preset_path(path)

    def _set_audio_label(self):
        self.audio_label.setText(f"{self.audio.label}\n{self.audio.sample_rate:,} Hz / {self.audio.channels} channels")

    def set_audio_path(self, path=None):
        try:
            replacement = AudioSource(path)
        except Exception as error:
            self._on_error(error)
            return
        self.audio.close()
        self.audio = replacement
        self._audio_ticks = 0
        self.error_label.clear()
        self._set_audio_label()
        self.statusBar().showMessage(f"PCM source / {self.audio.label}")
        if self._ready:
            self._audio_timer.start()

    @Slot()
    def choose_wav(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PCM WAV", "", "PCM WAV files (*.wav)")
        if path:
            self.set_audio_path(path)

    @Slot()
    def use_demo_audio(self):
        self.set_audio_path()

    @Slot(bool)
    def _pause_changed(self, paused):
        self.pause_button.setText("Resume PCM" if paused else "Pause PCM")

    def save_frame(self, path):
        if not self._ready:
            raise RuntimeError("Wait for the first rendered frame before saving")
        if self._last_frame is None:
            image = self.viewport.grabFramebuffer()
        else:
            frame = self._last_frame
            height, width, _ = frame.shape
            image = QImage(frame.data, width, height, frame.strides[0], QImage.Format.Format_RGBA8888).copy()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if image.isNull() or not image.save(str(path), "PNG"):
            raise RuntimeError(f"Could not save frame: {path}")
        self.statusBar().showMessage(f"Saved {path}", 5000)

    @Slot()
    def choose_snapshot(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save rendered frame", str(OUTPUT_DIR / "pyside6.png"),
                                             "PNG images (*.png)")
        if path:
            try:
                self.save_frame(path)
            except Exception as error:
                self._on_error(error)

    def eventFilter(self, watched, event):
        if watched is self.viewport and event.type() == QEvent.Type.Resize and not self._closing:
            self._resize_timer.start()
        return super().eventFilter(watched, event)

    @Slot()
    def _resize_worker(self):
        if self.worker is None or self._closing or not self.worker.is_alive():
            return
        ratio = self.viewport.devicePixelRatioF()
        size = (max(1, int(self.viewport.width() * ratio + 0.5)),
                max(1, int(self.viewport.height() * ratio + 0.5)))
        if size != self._requested_size:
            try:
                self.worker.resize(*size)
                self._requested_size = size
            except queue.Full:
                self._resize_timer.start()
            except Exception as error:
                self._on_error(error)

    @Slot()
    def _finish(self):
        try:
            if self.args.screenshot is not None:
                self.save_frame(self.args.screenshot)
        except Exception as error:
            self._on_error(error)
        print(f"PySide6 {self.args.mode} rendered {self.frame_count} frames")
        self.close()

    @Slot()
    def shutdown(self):
        if self._closing:
            return
        self._closing = True
        self._audio_timer.stop()
        self._resize_timer.stop()
        self._startup_timer.stop()
        try:
            if self.worker is not None:
                # Join on the GUI thread before its offscreen surface is destroyed.
                self.worker.close()
            else:
                # The widget's native context is still available at this point.
                self.viewport.cleanup()
                self.viewport.doneCurrent()
        finally:
            self.audio.close()

    def closeEvent(self, event):
        self.shutdown()
        super().closeEvent(event)


def main(argv=None):
    args = build_parser().parse_args(argv)
    # A compatible format must be selected before Qt creates its application/contexts.
    QSurfaceFormat.setDefaultFormat(opengl_format())
    app = QApplication(sys.argv[:1])
    app.setApplicationName("projectM Studio")
    window = None
    try:
        window = VisualizerWindow(args)
        window.show()
        app.exec()
        return window.exit_code
    except (Exception, KeyboardInterrupt) as error:
        print(f"PySide6: {error}", file=sys.stderr)
        return 130 if isinstance(error, KeyboardInterrupt) else 1
    finally:
        if window is not None:
            window.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
