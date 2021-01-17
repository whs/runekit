import abc
import logging
import time

from PIL import Image
from PySide2.QtGui import QGuiApplication

_debug_dump_file = False
logger = logging.getLogger(__name__)


class QtGrabMixin(abc.ABC):
    refresh_rate: int

    __game_last_grab = 0.0
    __game_last_image = None

    @abc.abstractmethod
    def get_wid(self) -> int:
        ...

    def grab_game(self) -> Image:
        if (time.monotonic() - self.__game_last_grab) * 1000 < self.refresh_rate:
            return self.__game_last_image

        screen = QGuiApplication.primaryScreen()
        pixmap = screen.grabWindow(self.get_wid())
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
