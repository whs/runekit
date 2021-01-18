import abc
from typing import List

from PySide2.QtCore import QObject, Property, Signal

from .instance import GameInstance


class GameManager(QObject):
    @abc.abstractmethod
    def get_instances(self) -> List[GameInstance]:
        ...

    instance_added = Signal()
    instance_removed = Signal()
    instance_changed = Signal()
    instances = Property(list, get_instances, notify=instance_changed)
