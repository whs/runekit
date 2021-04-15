import logging
import time
from typing import TYPE_CHECKING, List, Union

import xcffib.composite
import xcffib.xproto
from PySide2.QtCore import QRect, Signal, Slot
from PySide2.QtGui import QWindow, QGuiApplication
from PySide2.QtWidgets import QGraphicsItem

from runekit.game.instance import GameInstance
from runekit.game.psutil_mixins import PsUtilNetStat
from runekit.game.qt import QtGrabMixin, QtEmbedMixin
from .ximage import zpixmap_shm_to_image

if TYPE_CHECKING:
    from .manager import X11GameManager


class X11GameInstance(QtGrabMixin, QtEmbedMixin, PsUtilNetStat, GameInstance):
    wid: int
    refresh_rate = 100

    manager: "X11GameManager"
    overlay: QGraphicsItem

    game_last_grab = 0.0
    game_last_image = None
    embedded_windows: List[QWindow]
    cached_position = None

    input_signal = Signal(xcffib.Event)
    config_signal = Signal(xcffib.Event)
    destroy_signal = Signal(xcffib.Event)

    def __init__(self, manager: "X11GameManager", wid: int, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.wid = wid
        self.pid = manager.get_property(wid, "_NET_WM_PID")
        self.qwindow = QWindow.fromWinId(wid)
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.embedded_windows = []
        self._setup_x()
        self._setup_overlay()

        self.input_signal.connect(self.on_input)
        self.config_signal.connect(self.on_config)

        self._update_is_focused()

    def _setup_x(self):
        self.manager.xcomposite.RedirectWindow(
            self.wid, xcffib.composite.Redirect.Automatic
        )
        self.name_pixmap()
        self.manager.connection.core.ChangeWindowAttributesChecked(
            self.wid,
            xcffib.xproto.CW.EventMask,
            [
                xcffib.xproto.EventMask.KeyPress
                | xcffib.xproto.EventMask.StructureNotify
            ],
        )

    def _setup_overlay(self):
        self.overlay, self._overlay_disconnect = self.manager.overlay.add_instance(self)

    def __del__(self):
        self.manager.connection.core.FreePixmap(self.pixmap_id)
        self.manager.xcomposite.UnredirectWindow(
            self.wid, xcffib.composite.Redirect.Automatic
        )
        self._overlay_disconnect()

    def name_pixmap(self):
        if hasattr(self, "pixmap_id"):
            self.manager.connection.core.FreePixmap(self.pixmap_id)

        self.pixmap_id = self.manager.connection.generate_id()
        self.manager.xcomposite.NameWindowPixmap(
            self.wid, self.pixmap_id, is_checked=True
        )

    def get_position(self) -> QRect:
        if self.cached_position:
            return self.cached_position

        geom = self.manager.connection.core.GetGeometry(self.wid).reply()
        translated = self.manager.connection.core.TranslateCoordinates(
            self.wid, self.manager.screen.root, 0, 0
        ).reply()

        self.cached_position = QRect(
            translated.dst_x, translated.dst_y, geom.width, geom.height
        )
        return self.cached_position

    def get_scaling(self) -> float:
        pos = self.get_position().topLeft()
        if pos.x() < 0:
            pos.setX(0)
        if pos.y() < 0:
            pos.setY(0)

        screen = QGuiApplication.screenAt(pos)
        return screen.devicePixelRatio()

    def is_focused(self) -> bool:
        return self._is_focused

    def _update_is_focused(self):
        self._is_focused = self.manager.get_active_window() == self.wid

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

    def embed_window(self, window: QWindow):
        super().embed_window(window)
        self.embedded_windows.append(window)

    def get_overlay_area(self) -> QGraphicsItem:
        return self.overlay

    @Slot(xcffib.Event)
    def on_config(self, evt: xcffib.xproto.ConfigureNotifyEvent):
        self.name_pixmap()

        translated = self.manager.connection.core.TranslateCoordinates(
            self.wid, self.manager.screen.root, 0, 0
        ).reply()
        size = QRect(translated.dst_x, translated.dst_y, evt.width, evt.height)

        self.cached_position = size
        self.positionChanged.emit(size)

    @Slot(xcffib.Event)
    def on_input(
        self, evt: Union[xcffib.xproto.KeyPressEvent, xcffib.xproto.ButtonPressEvent]
    ):
        if evt.detail == 10 and evt.state & xcffib.xproto.KeyButMask.Mod1:
            self.alt1_pressed.emit()
        else:
            self.game_activity.emit()
