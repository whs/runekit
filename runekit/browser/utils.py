import base64
from typing import TypeVar

import numpy as np
from PIL import Image
from PySide2.QtGui import QColor

from runekit.game.instance import ImageType
from runekit.image.np_utils import np_crop

TRANSFER_LIMIT = 4_000_000


class ApiPermissionDeniedException(Exception):
    required_permission: str

    def __init__(self, required_permission: str):
        super().__init__(
            "Permission '%s' is needed for this action".format(required_permission)
        )
        self.required_permission = required_permission


ImgTypeG = TypeVar("T", np.ndarray, Image.Image)


def ensure_image_rgba(image: ImgTypeG) -> ImgTypeG:
    # XXX: This function is not idempotent!
    if isinstance(image, np.ndarray):
        return image[:, :, [2, 1, 0, 3]]
    else:
        if image.mode == "RGB":
            image = image.convert("RGBA")

        return image


def ensure_image_bgra(image: ImgTypeG) -> ImgTypeG:
    # XXX: This function is not idempotent!
    if isinstance(image, np.ndarray):
        return image
    else:
        if image.mode == "RGB":
            image = image.convert("RGBA")

        r, g, b, a = image.split()
        image = Image.merge("RGBA", (b, g, r, a))

        return image


def ensure_image(image: ImgTypeG, mode: str) -> ImgTypeG:
    if mode == "rgba":
        return ensure_image_rgba(image)
    elif mode == "bgra":
        return ensure_image_bgra(image)
    else:
        raise ValueError("invalid mode")


def image_to_stream(
    image: ImageType,
    x=0,
    y=0,
    width=None,
    height=None,
    mode="bgra",
    ignore_limit=False,
) -> bytes:
    if isinstance(image, np.ndarray):
        out = np_crop(image, x, y, width, height)
        out = ensure_image(out, mode).tobytes()
    else:
        assert image.mode == "RGBA"

        if width is None:
            width = image.width
        if height is None:
            height = image.height

        if not ignore_limit and width * height * 4 > TRANSFER_LIMIT:
            return ""

        image = image.crop((x, y, x + width, y + height))

        out = ensure_image(image, mode).tobytes()

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
    img = base64.b64decode(img)
    img = np.frombuffer(img, "<B")
    img.shape = (-1, width, 4)
    return img
