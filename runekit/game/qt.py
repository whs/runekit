import logging
import time

import numpy as np
from PySide2.QtCore import QBuffer, QIODevice
from PySide2.QtGui import QGuiApplication, QWindow, QPixmap
import cv2

from runekit.image.np_utils import np_save_image

_debug_dump_file = False
logger = logging.getLogger(__name__)


def qpixmap_to_np(im: QPixmap) -> np.ndarray:
    # from PIL.ImageQt.fromqimage
    buffer = QBuffer()
    buffer.open(QIODevice.ReadWrite)
    if im.hasAlphaChannel():
        im.save(buffer, "png")
    else:
        im.save(buffer, "ppm")

    npbuf = np.frombuffer(buffer.data(), "<B")
    buffer.close()

    out = cv2.imdecode(npbuf, cv2.IMREAD_UNCHANGED)
    if out.shape[2] == 3:
        # Add alpha channel
        out = np.pad(out, ((0, 0), (0, 0), (0, 1)), constant_values=0xFF)

    return out


class QtBaseMixin:
    qwindow: QWindow


class QtGrabMixin(QtBaseMixin):
    refresh_rate: int

    __game_last_grab = 0.0
    __game_last_image = None

    def grab_game(self) -> np.ndarray:
        if (time.monotonic() - self.__game_last_grab) * 1000 < self.refresh_rate:
            return self.__game_last_image

        screen = QGuiApplication.primaryScreen()
        pixmap = screen.grabWindow(self.qwindow.winId())
        image = qpixmap_to_np(pixmap)

        if _debug_dump_file:
            logger.debug("dumping file")
            np_save_image(image, "/tmp/qtshot.bmp")

        self.__game_last_image = image
        self.__game_last_grab = time.monotonic()
        return self.__game_last_image

    def grab_desktop(self, x, y, w, h) -> np.ndarray:
        screen = QGuiApplication.primaryScreen()
        pixmap = screen.grabWindow(0, x, y, w, h)
        image = qpixmap_to_np(pixmap)

        if _debug_dump_file:
            logger.debug("dumping file")
            np_save_image(image, "/tmp/qtshot.bmp")

        return image


class QtEmbedMixin(QtBaseMixin):
    def embed_window(self, window: QWindow):
        window.setParent(self.qwindow)
