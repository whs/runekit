import abc
import time
from typing import TYPE_CHECKING, Literal, Optional, Union

import numpy as np
from PIL import Image
from PySide2.QtCore import QObject, Signal, Property, QRect, Slot
from PySide2.QtGui import QWindow
from PySide2.QtWidgets import QGraphicsItem

from runekit.image.np_utils import np_crop

if TYPE_CHECKING:
    from .manager import GameManager

PROGRESS_TYPE = Literal["RESET", "IN_PROGRESS", "ERROR", "LOADING", "PAUSED"]
ImageType = Union[np.ndarray, Image.Image]


class GameInstance(QObject):
    refresh_rate = 1000
    manager: "GameManager"
    _last_game_activity: float = 0

    alt1_pressed = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_activity.connect(self.on_game_activity)

    def get_last_game_activity(self) -> float:
        return self._last_game_activity

    @Slot()
    def on_game_activity(self):
        self._last_game_activity = time.monotonic()

    game_activity = Signal()
    last_game_activity = Property(float, get_last_game_activity, notify=game_activity)

    @abc.abstractmethod
    def get_position(self) -> QRect:
        """Return the game window position, without space used by window decoration"""
        ...

    positionChanged = Signal(QRect)
    position = Property(QRect, get_position, notify=positionChanged)

    @abc.abstractmethod
    def get_scaling(self) -> float:
        ...

    scalingChanged = Signal(float)
    scaling = Property(float, get_scaling, notify=scalingChanged)

    @abc.abstractmethod
    def is_focused(self) -> bool:
        ...

    focusChanged = Signal(bool)
    focused = Property(bool, is_focused, notify=focusChanged)

    @abc.abstractmethod
    def get_world(self) -> Optional[int]:
        ...

    worldChanged = Signal(int)
    world = Property(int, get_world, notify=worldChanged)

    @abc.abstractmethod
    def grab_game(self) -> ImageType:
        ...

    @abc.abstractmethod
    def grab_desktop(self, x: int, y: int, w: int, h: int) -> ImageType:
        ...

    def grab_region(self, x: int, y: int, w: int, h: int) -> ImageType:
        image = self.grab_game()

        if isinstance(image, np.ndarray):
            return np_crop(image, x, y, w, h)
        else:
            return image.crop((x, y, x + w, y + h))

    def set_taskbar_progress(self, type_: PROGRESS_TYPE, progress: float):
        pass

    def embed_window(self, window: QWindow):
        pass

    def get_overlay_area(self) -> QGraphicsItem:
        raise NotImplementedError
