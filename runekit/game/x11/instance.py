from PySide2.QtGui import QWindow
from Xlib.xobject.drawable import Window

from runekit.game.instance import GameInstance
from runekit.game.qt import QtGrabMixin, QtWindowMixin, QtWindowEventMixin


class X11GameInstance(QtGrabMixin, QtWindowMixin, QtWindowEventMixin, GameInstance):
    _xwindow: Window

    def __init__(self, window: Window):
        super().__init__()
        self._xwindow = window
        self.qwindow = QWindow.fromWinId(self._xwindow.id)
        self._bind_window_events()

    def set_taskbar_progress(self, type_, progress):
        # Not supported
        pass
