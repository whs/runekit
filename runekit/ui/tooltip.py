from typing import Union

from PySide2.QtCore import Qt, QTimer, Slot
from PySide2.QtGui import QCursor
from PySide2.QtWidgets import QLabel, QMainWindow


class TooltipManager(QMainWindow):
    timer: QTimer

    pad_x = 5
    pad_y = 20
    poll_interval = 10
    opacity = 0.8

    def __init__(self):
        super().__init__(
            flags=Qt.Popup
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
        )
        self._layout()
        self.timer = QTimer(self)
        self.timer.setInterval(self.poll_interval)
        self.timer.timeout.connect(self.update_position)
        self.setWindowOpacity(self.opacity)

    def _layout(self):
        self.label = QLabel(parent=self)
        self.label.setMargin(12)
        self.setCentralWidget(self.label)

    def set_tooltip(self, text: Union[str, None]):
        """Set and show tooltip. Set to empty string to hide"""
        if not text:
            self.hide()
            self.timer.stop()
            self.label.setText("")
            return

        self.label.setText(text)
        self.setFixedSize(self.label.sizeHint())
        self.show()
        self.update_position()
        self.timer.start()

    @Slot()
    def update_position(self):
        if not self.isVisible():
            return

        pos = QCursor.pos()
        self.move(pos.x() + self.pad_x, pos.y() + self.pad_y)
