import Quartz
from PIL import Image
from PySide2.QtCore import QRect
from PySide2.QtGui import QGuiApplication

from ..instance import GameInstance

_debug_dump_file = False

def cgrectref_to_qrect(cgrect) -> QRect:
    return QRect(cgrect["X"], cgrect["Y"], cgrect["Width"], cgrect["Height"])

def cgimageref_to_image(imgref) -> Image:
    w = Quartz.CGImageGetWidth(imgref)
    h = Quartz.CGImageGetHeight(imgref)
    raw = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(imgref))

    image = Image.frombuffer("RGBA", (w, h), raw, "raw", "RGBA", 0, 1)
    b, g, r, a = image.split()
    out = Image.merge("RGBA", (r, g, b, a))

    if _debug_dump_file:
        out.save('/tmp/game.bmp')

    return out

class QuartzGameInstance(GameInstance):
    def __init__(self, manager, wid, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.wid = wid

    def get_position(self) -> QRect:
        infos = Quartz.CGWindowListCreateDescriptionFromArray([self.wid])
        info = infos[0]  # FIXME: what if window closed
        return cgrectref_to_qrect(info[Quartz.kCGWindowBounds])

    def get_scaling(self) -> float:
        screen = QGuiApplication.screenAt(self.get_position().topLeft())
        return screen.devicePixelRatio()

    def is_active(self) -> bool:
        return True  # FIXME

    def grab_game(self) -> Image:
        imgref = Quartz.CGWindowListCreateImageFromArray(
            Quartz.CGRectNull,
            [self.wid],
            Quartz.kCGWindowImageBoundsIgnoreFraming,
        )
        out = cgimageref_to_image(imgref)
        scale = self.get_scaling()
        if scale > 1:
            out = out.resize((int(out.width / scale), int(out.height / scale)), Image.NEAREST)
        return out

    def grab_desktop(self, x: int, y: int, w: int, h: int) -> Image:
        imgref = Quartz.CGWindowListCreateImage(
            Quartz.CGRect(Quartz.CGPoint(x, y), Quartz.CGSize(w, h)),
            Quartz.kCGWindowListOptionAll,
            Quartz.kCGNullWindowID,
            Quartz.kCGWindowImageDefault,
        )
        out = cgimageref_to_image(imgref)
        return out.resize((w, h), Image.NEAREST)

    def set_taskbar_progress(self, type, progress):
        pass
