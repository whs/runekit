from PySide2.QtCore import QPoint
from PySide2.QtGui import QGuiApplication
from Xlib.xobject.drawable import Window

from runekit.game.instance import GameInstance, WindowPosition
from runekit.game.qt import QtGrabMixin


class X11GameInstance(QtGrabMixin, GameInstance):
    def __init__(self, window: Window):
        self.window = window

    def get_wid(self) -> int:
        return self.window.id

    def get_position(self) -> WindowPosition:
        geom = self.window.get_geometry()
        screen = QGuiApplication.screenAt(QPoint(geom.x, geom.y))
        scaling = screen.devicePixelRatio()

        return WindowPosition(
            x=geom.x,
            y=geom.y,
            width=geom.width,
            height=geom.height,
            scaling=scaling,
        )

    def set_taskbar_progress(self, type_, progress):
        # Not supported
        pass
