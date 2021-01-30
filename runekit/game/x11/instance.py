import logging
import time
from typing import TYPE_CHECKING

from PySide2.QtCore import QRect, Slot, Signal
from PySide2.QtGui import QWindow, QGuiApplication
import xcffib.xproto
import xcffib.composite
import xcffib.xinput
from PIL import Image, ImageOps

from runekit.game.instance import GameInstance
from runekit.game.qt import QtGrabMixin
from .ximage import zpixmap_shm_to_image

if TYPE_CHECKING:
    from .manager import X11GameManager

KEY_1 = 10


class X11GameInstance(QtGrabMixin, GameInstance):
    wid: int

    manager: "X11GameManager"

    game_last_grab = 0.0
    game_last_image = None

    key_press = Signal(xcffib.xinput.KeyPressEvent)

    def __init__(self, manager: "X11GameManager", wid: int, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.wid = wid
        self.qwindow = QWindow.fromWinId(wid)
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self._setup()
        self.key_press.connect(self.on_key_press)
        self._update_is_focused()

    def _setup(self):
        self.manager.xcomposite.RedirectWindow(
            self.wid, xcffib.composite.Redirect.Automatic
        )
        self.pixmap_id = self.manager.connection.generate_id()
        self.manager.xcomposite.NameWindowPixmap(
            self.wid, self.pixmap_id, is_checked=True
        )

        self._grab_alt1()
        # self.manager.xinput.XIGrabDevice(
        #     self.wid,
        #     xcffib.xproto.Time.CurrentTime,
        #     xcffib.xproto.Cursor._None,
        #     xcffib.xinput.Device.All,
        #     xcffib.xinput.GrabMode22.Async,
        #     xcffib.xinput.GrabMode22.Async,
        #     True,
        #     1,
        #     (
        #         xcffib.xinput.XIEventMask.KeyPress
        #         | xcffib.xinput.XIEventMask.ButtonPress,
        #     ),
        # )

    def _grab_alt1(self):
        self.manager.xinput.XIPassiveGrabDevice(
            xcffib.xproto.Time.CurrentTime,
            self.wid,
            xcffib.xproto.Cursor._None,
            KEY_1,
            xcffib.xinput.Device.All,
            1,
            1,
            xcffib.xinput.GrabType.Keycode,
            xcffib.xinput.GrabMode22.Async,
            xcffib.xproto.GrabMode.Async,
            True,
            (
                xcffib.xinput.XIEventMask.KeyPress
                | xcffib.xinput.XIEventMask.KeyRelease,
            ),
            (xcffib.xproto.KeyButMask.Mod1,),
        )

    def _ungrab_alt1(self):
        self.manager.xinput.XIPassiveUngrabDevice(
            self.wid,
            KEY_1,
            xcffib.xinput.Device.All,
            1,
            xcffib.xinput.GrabType.Keycode,
            (xcffib.xproto.KeyButMask.Mod1,),
        )

    def __del__(self):
        self.manager.connection.core.FreePixmap(self.pixmap_id)
        self.manager.xcomposite.UnredirectWindow(
            self.wid, xcffib.composite.Redirect.Automatic
        )
        self._ungrab_alt1()

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

    @Slot(xcffib.xinput.KeyPressEvent)
    def on_key_press(self, evt: xcffib.xinput.KeyPressEvent):
        # Check for alt1
        if evt.flags & xcffib.xinput.KeyEventFlags.KeyRepeat:
            return

        if evt.mods.effective & xcffib.xproto.KeyButMask.Mod1 and evt.detail == KEY_1:
            if isinstance(evt, xcffib.xinput.KeyPressEvent):
                self.alt1_pressed.emit()
                self.logger.debug("alt1 pressed %s", repr(evt))
            else:
                self._ungrab_alt1()
                self._grab_alt1()

            return

    def grab_game(self):
        if (time.monotonic() - self.game_last_grab) * 1000 < self.refresh_rate:
            return self.game_last_image

        xid = shm = None
        try:
            geom = self.manager.connection.core.GetGeometry(self.pixmap_id).reply()
            xid, shm = self.manager.get_shm(geom.width * geom.height * 4)
            size = (
                self.manager.xshm.GetImage(
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
