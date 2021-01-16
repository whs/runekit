import abc
from typing import List

from .instance import GameInstance


class GameManager(abc.ABC):
    @abc.abstractmethod
    def get_instances(self) -> List[GameInstance]:
        ...
