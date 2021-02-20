import base64 as b64
from typing import Union

import numpy as np
from PIL import Image
from PySide2.QtGui import QColor

from runekit.image.np_utils import np_crop

TRANSFER_LIMIT = 4_000_000


class ApiPermissionDeniedException(Exception):
    required_permission: str

    def __init__(self, required_permission: str):
        super().__init__(
            "Permission '%s' is needed for this action".format(required_permission)
        )
        self.required_permission = required_permission


def image_to_stream(
    image: Union[Image.Image, np.ndarray],
    x=0,
    y=0,
    width=None,
    height=None,
    base64=True,
) -> bytes:
    if isinstance(image, np.ndarray):
        out = np_crop(image, x, y, width, height).tobytes()
    else:
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

        out = image.tobytes()

    if base64:
        return b64.b64encode(out)

    return out


def encode_mouse(x: int, y: int) -> int:
    return (x << 16) | y


def decode_color(color: int) -> QColor:
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = (color >> 0) & 0xFF
    a = (color >> 24) & 0xFF
    return QColor.fromRgb(r, g, b, a)


def decode_image(img: str, width: int) -> np.ndarray:
    img = b64.b64decode(img)
    img = np.frombuffer(img, "<B")
    img.shape = (-1, width, 4)
    return img
