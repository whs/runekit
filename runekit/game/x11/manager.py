from typing import List, Dict

from .instance import GameInstance, X11GameInstance
from Xlib.display import Display


class X11GameManager:
    display: Display

    _instance: Dict[int, GameInstance]

    def __init__(self):
        self.display = Display()
        self._instance = {}

    def get_instances(self) -> List[GameInstance]:
        out = []

        def visit(window):
            wm_class = window.get_wm_class()
            if wm_class and wm_class[0] == "RuneScape":
                if window.id not in self._instance:
                    self._instance[window.id] = X11GameInstance(window)
                out.append(self._instance[window.id])

            for child in window.query_tree().children:
                visit(child)

        for index in range(self.display.screen_count()):
            visit(self.display.screen(index).root)

        return out
