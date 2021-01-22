from typing import TYPE_CHECKING

from PySide2.QtCore import QRect
from PySide2.QtGui import QWindow, QGuiApplication
from Xlib.xobject.drawable import Window

from runekit.game.instance import GameInstance
from runekit.game.qt import QtGrabMixin

if TYPE_CHECKING:
    from .manager import X11GameManager


class X11GameInstance(QtGrabMixin, GameInstance):
    xwindow: Window

    manager: "X11GameManager"

    def __init__(self, manager: "X11GameManager", window: Window, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.xwindow = window
        self.qwindow = QWindow.fromWinId(self.xwindow.id)
        self._update_is_focused()

    def get_position(self) -> QRect:
        geom = self.xwindow.get_geometry()

        return QRect(geom.x, geom.y, geom.width, geom.height)

    def get_scaling(self) -> float:
        screen = QGuiApplication.screenAt(self.get_position().topLeft())
        return screen.devicePixelRatio()

    def is_focused(self) -> bool:
        return self.is_focused

    def _update_is_focused(self):
        self.is_focused = self.manager.get_active_window() == self.xwindow.id

    def set_taskbar_progress(self, type_, progress):
        # Not supported
        pass
