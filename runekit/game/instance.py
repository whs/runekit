import abc
import dataclasses
import time
from typing import TYPE_CHECKING

from PySide2.QtCore import QObject, Signal, Property, QRect, Slot

from PIL import Image

if TYPE_CHECKING:
    from .manager import GameManager


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
    def grab_game(self) -> Image:
        ...

    @abc.abstractmethod
    def grab_desktop(self, x: int, y: int, w: int, h: int) -> Image:
        ...

    def grab_region(self, x: int, y: int, w: int, h: int) -> Image:
        image = self.grab_game()
        return image.crop((x, y, x + w, y + h))

    @abc.abstractmethod
    def set_taskbar_progress(self, type, progress):
        ...
