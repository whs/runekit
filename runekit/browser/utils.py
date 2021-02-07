import base64

from PIL import Image
from PySide2.QtGui import QColor

TRANSFER_LIMIT = 4_000_000


class ApiPermissionDeniedException(Exception):
    required_permission: str

    def __init__(self, required_permission: str):
        super().__init__(
            "Permission '%s' is needed for this action".format(required_permission)
        )
        self.required_permission = required_permission


def image_to_stream(image: Image, x=0, y=0, width=None, height=None) -> bytes:
    assert image.mode == "RGB" or image.mode == "RGBA"

    if width is None:
        width = image.width
    if height is None:
        height = image.height

    if width * height * 4 > TRANSFER_LIMIT:
        return ""

    if image.mode == "RGB":
        image = image.convert("RGBA")

    r, g, b, a = image.crop((x, y, x + width, y + height)).split()
    image = Image.merge("RGBA", (b, g, r, a))

    return base64.b64encode(image.tobytes())


def encode_mouse(x: int, y: int) -> int:
    return (x << 16) | y


def decode_color(color: int) -> QColor:
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = (color >> 0) & 0xFF
    a = (color >> 24) & 0xFF
    return QColor.fromRgb(r, g, b, a)
