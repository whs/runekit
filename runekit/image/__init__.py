import logging
import struct
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

try:
    from .format import image_to_bgra
except ImportError:
    logging.warning("Cannot import native image code, using pure python")

    image_8bpp = struct.Struct("BBBB")

    def image_to_bgra(image: "Image", x, y, w, h) -> bytes:
        buf = bytearray(w * h * image_8bpp.size)
        index = 0
        for p in image.crop((x, y, x + w, y + h)).getdata():
            r = p[0]
            g = p[1]
            b = p[2]
            a = p[3] if len(p) == 4 else 255

            image_8bpp.pack_into(buf, index, b, g, r, a)
            index += image_8bpp.size

        return buf
