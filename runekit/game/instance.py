import abc
import dataclasses
from typing import TYPE_CHECKING

from PySide2.QtCore import QObject, Signal, Property, QRect

from PIL import Image

if TYPE_CHECKING:
    from .manager import GameManager


class GameInstance(QObject):
    refresh_rate = 1000
    manager: "GameManager"

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
    def is_active(self) -> bool:
        ...

    activeChanged = Signal(bool)
    active = Property(bool, is_active, notify=activeChanged)

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
