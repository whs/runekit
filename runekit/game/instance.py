import abc
import dataclasses

from PIL import Image


@dataclasses.dataclass
class WindowPosition:
    x: int
    y: int
    width: int
    height: int
    scaling: int


class GameInstance(abc.ABC):
    refresh_rate = 1000

    @abc.abstractmethod
    def get_position(self) -> WindowPosition:
        ...

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
