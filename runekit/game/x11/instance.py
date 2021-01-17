from typing import TYPE_CHECKING

from PySide2.QtCore import QPoint
from PySide2.QtGui import QWindow, QGuiApplication
from Xlib.xobject.drawable import Window

from runekit.game.instance import GameInstance, WindowPosition
from runekit.game.qt import QtGrabMixin

if TYPE_CHECKING:
    from .manager import X11GameManager


class X11GameInstance(QtGrabMixin, GameInstance):
    xwindow: Window
    manager: "X11GameManager"

    def __init__(self, manager: "X11GameManager", window: Window):
        super().__init__()
        self.manager = manager
        self.xwindow = window
        self.qwindow = QWindow.fromWinId(self.xwindow.id)

    def get_position(self) -> WindowPosition:
        geom = self.xwindow.get_geometry()

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
        return self.manager.get_active_window() == self.xwindow.id

    def set_taskbar_progress(self, type_, progress):
        # Not supported
        pass
