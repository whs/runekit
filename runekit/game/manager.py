import abc
from typing import List, Union

from PySide2.QtCore import QObject, Property, Signal

from .instance import GameInstance


class GameManager(QObject):
    @abc.abstractmethod
    def get_instances(self) -> List[GameInstance]:
        """Return a list of active game instance. The instances returned should be stable (same instance for all invocation)"""
        ...

    @abc.abstractmethod
    def get_active_instance(self) -> Union[GameInstance, None]:
        ...

    instance_added = Signal(GameInstance)
    instance_removed = Signal(GameInstance)
    instance_changed = Signal()
    instances = Property(list, get_instances, notify=instance_changed)

    def stop(self):
        """Stop the GameManager and any GameInstances"""
        pass
