import logging
import time
from typing import TYPE_CHECKING

from PySide2.QtCore import QRect
from PySide2.QtGui import QWindow, QGuiApplication
import xcffib.xproto
import xcffib.composite
from PIL import Image, ImageOps

from runekit.game.instance import GameInstance
from runekit.game.qt import QtGrabMixin
from .ximage import zpixmap_shm_to_image

if TYPE_CHECKING:
    from .manager import X11GameManager


class X11GameInstance(QtGrabMixin, GameInstance):
    wid: int

    manager: "X11GameManager"

    game_last_grab = 0.0
    game_last_image = None

    def __init__(self, manager: "X11GameManager", wid: int, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.wid = wid
        self.qwindow = QWindow.fromWinId(wid)
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self._setup()
        self._update_is_focused()

    def _setup(self):
        self.manager.composite.RedirectWindow(
            self.wid, xcffib.composite.Redirect.Automatic
        )
        self.pixmap_id = self.manager.connection.generate_id()
        self.manager.composite.NameWindowPixmap(
            self.wid, self.pixmap_id, is_checked=True
        )

    def __del__(self):
        self.manager.connection.core.FreePixmap(self.pixmap_id)
        self.manager.composite.UnredirectWindow(
            self.wid, xcffib.composite.Redirect.Automatic
        )

    def get_position(self) -> QRect:
        geom = self.manager.connection.core.GetGeometry(self.wid).reply()

        return QRect(geom.x, geom.y, geom.width, geom.height)

    def get_scaling(self) -> float:
        screen = QGuiApplication.screenAt(self.get_position().topLeft())
        return screen.devicePixelRatio()

    def is_focused(self) -> bool:
        return self.is_focused

    def _update_is_focused(self):
        self.is_focused = self.manager.get_active_window() == self.wid

    def set_taskbar_progress(self, type_, progress):
        # TODO: Implement this on Unity? I don't use Unity
        # TODO: If progress = 1 set urgency flag
        pass

    def grab_game(self):
        if (time.monotonic() - self.game_last_grab) * 1000 < self.refresh_rate:
            return self.game_last_image

        xid = shm = None
        try:
            geom = self.manager.connection.core.GetGeometry(self.pixmap_id).reply()
            xid, shm = self.manager.get_shm(geom.width * geom.height * 4)
            size = (
                self.manager.shm.GetImage(
                    self.pixmap_id,
                    0,
                    0,
                    geom.width,
                    geom.height,
                    0xFFFFFF,
                    xcffib.xproto.ImageFormat.ZPixmap,
                    xid,
                    0,
                )
                .reply()
                .size
            )

            out = zpixmap_shm_to_image(shm, size, geom.width, geom.height)

            self.game_last_image = out
            self.game_last_grab = time.monotonic()

            return out
        finally:
            if shm:
                self.manager.free_shm((xid, shm))
