from PySide2.QtCore import QPoint
from PySide2.QtGui import QWindow, QGuiApplication
from Xlib.xobject.drawable import Window

from runekit.game.instance import GameInstance, WindowPosition
from runekit.game.qt import QtGrabMixin


class X11GameInstance(QtGrabMixin, GameInstance):
    _xwindow: Window

    def __init__(self, window: Window):
        super().__init__()
        self._xwindow = window
        self.qwindow = QWindow.fromWinId(self._xwindow.id)

    def get_position(self) -> WindowPosition:
        geom = self._xwindow.get_geometry()

        screen = QGuiApplication.screenAt(QPoint(geom.x, geom.y))
        scaling = screen.devicePixelRatio()

        return WindowPosition(
            x=geom.x,
            y=geom.y,
            width=geom.width,
            height=geom.height,
            scaling=scaling,
        )

    def is_active(self) -> bool:
        return True

    def set_taskbar_progress(self, type_, progress):
        # Not supported
        pass
