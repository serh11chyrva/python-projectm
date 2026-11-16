import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import QWidget


class NumpyViewport(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: QPixmap | None = None

    def set_frame(self, frame: np.ndarray):
        h, w, _ = frame.shape

        image = QImage(
            frame.data,
            w,
            h,
            4 * w,
            QImage.Format_RGBA8888,
        )

        self._pixmap = QPixmap.fromImage(image)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        if self._pixmap:
            painter.drawPixmap(
                self.rect(),
                self._pixmap,
                self._pixmap.rect(),
            )
        else:
            painter.fillRect(self.rect(), Qt.black)
