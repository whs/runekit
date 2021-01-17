import abc
from typing import List

from pymitter import EventEmitter

from .instance import GameInstance


class GameManager(EventEmitter, abc.ABC):
    @abc.abstractmethod
    def get_instances(self) -> List[GameInstance]:
        ...
