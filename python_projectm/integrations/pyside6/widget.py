"""Display CPU RGBA frames on the Qt GUI thread."""

import numpy as np
from PySide6.QtCore import QRect, Qt, Slot
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from python_projectm.integrations.pyside6.context import require_gui_thread


class NumpyViewport(QWidget):
    def __init__(self, parent=None, *, keep_aspect: bool = False):
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self.keep_aspect = keep_aspect

    @Slot(object)
    def set_frame(self, frame: np.ndarray) -> None:
        require_gui_thread()
        if (
            not isinstance(frame, np.ndarray) or frame.dtype != np.uint8
            or frame.ndim != 3 or frame.shape[2] != 4
            or frame.shape[0] == 0 or frame.shape[1] == 0
        ):
            raise ValueError("frame must be a nonempty uint8 RGBA array of shape (height, width, 4)")
        frame = np.ascontiguousarray(frame)
        height, width, _ = frame.shape
        # Detach before returning: the producer may reuse or release the NumPy array.
        image = QImage(
            frame.data, width, height, frame.strides[0], QImage.Format.Format_RGBA8888
        ).copy()
        self._pixmap = QPixmap.fromImage(image)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        if self._pixmap is not None:
            target = self.rect()
            if self.keep_aspect:
                size = self._pixmap.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
                target = QRect(0, 0, size.width(), size.height())
                target.moveCenter(self.rect().center())
            painter.drawPixmap(target, self._pixmap, self._pixmap.rect())
