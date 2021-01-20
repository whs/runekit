import sys
from .instance import GameInstance
from .manager import GameManager


def get_platform_manager() -> GameManager:
    if sys.platform == "linux":
        from .x11.manager import X11GameManager

        return X11GameManager()
    elif sys.platform == "darwin":
        from .quartz.manager import QuartzGameManager

        return QuartzGameManager()

    raise NotImplementedError
