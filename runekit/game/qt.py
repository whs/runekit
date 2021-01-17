import abc
import logging
import time

from PIL import Image
from PySide2.QtCore import Slot
from PySide2.QtGui import QGuiApplication, QWindow, QScreen
from pymitter import EventEmitter

from runekit.game.instance import WindowPosition

_debug_dump_file = False
logger = logging.getLogger(__name__)


class QtBaseMixin(abc.ABC):
    qwindow: QWindow


class QtGrabMixin(QtBaseMixin):
    refresh_rate: int

    __game_last_grab = 0.0
    __game_last_image = None

    def grab_game(self) -> Image:
        if (time.monotonic() - self.__game_last_grab) * 1000 < self.refresh_rate:
            return self.__game_last_image

        screen = QGuiApplication.primaryScreen()
        pixmap = screen.grabWindow(self.qwindow.winId())
        image = Image.fromqpixmap(pixmap)

        if _debug_dump_file:
            logger.debug("dumping file")
            pixmap.save("qtshot.bmp", None, 100)

        self.__game_last_image = image
        self.__game_last_grab = time.monotonic()
        return self.__game_last_image

    def grab_desktop(self, x, y, w, h) -> Image:
        screen = QGuiApplication.primaryScreen()
        pixmap = screen.grabWindow(0, x, y, w, h)
        image = Image.fromqpixmap(pixmap)

        if _debug_dump_file:
            logger.debug("dumping file")
            pixmap.save("qtshot.bmp", None, 100)

        return image


class QtWindowMixin(QtBaseMixin):
    def is_active(self) -> bool:
        return self.qwindow.isActive()

    def get_position(self) -> WindowPosition:
        geom = self.qwindow.geometry()

        return WindowPosition(
            x=geom.x(),
            y=geom.y(),
            width=geom.width(),
            height=geom.height(),
            scaling=self.qwindow.devicePixelRatio(),
        )


class QtWindowEventMixin(EventEmitter, QtBaseMixin):
    def _bind_window_events(self):
        self.qwindow.activeChanged.connect(self.on_window_active)
        self.qwindow.widthChanged.connect(self.on_resize)
        self.qwindow.heightChanged.connect(self.on_resize)
        self.qwindow.screenChanged.connect(self.on_scaling_changed)
        self.qwindow.xChanged.connect(self.on_move)
        self.qwindow.yChanged.connect(self.on_move)

    @Slot()
    def on_window_active(self):
        print(self.qwindow.active())
        self.emit("active", self.qwindow.active())

    @Slot(int)
    def on_resize(self, _):
        print("resize")
        self.emit("resize", (self.qwindow.width(), self.qwindow.height()))

    @Slot(QScreen)
    def on_scaling_changed(self, _):
        print("scale")
        self.emit("scalingChange", self.qwindow.devicePixelRatio())

    @Slot(int)
    def on_move(self, _):
        print("move")
        self.emit("move", (self.qwindow.x(), self.qwindow.y()))
