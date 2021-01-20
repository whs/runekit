from typing import List, Dict

import Quartz

from ..instance import GameInstance
from ..manager import GameManager
from .instance import QuartzGameInstance


class QuartzGameManager(GameManager):
    _instances: Dict[int, GameInstance]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._instances = {}

    def get_instances(self) -> List[GameInstance]:
        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID
        )

        for window in windows:
            if window[Quartz.kCGWindowOwnerName] == "rs2client":
                wid = window[Quartz.kCGWindowNumber]
                if wid not in self._instances:
                    self._instances[wid] = QuartzGameInstance(self, wid, parent=self)

        return list(self._instances.values())
