from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from runekit.game.instance import ImageType


def np_crop(image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
    shape = image.shape
    img_width = shape[1]
    img_height = shape[0]
    if w is None:
        w = img_width
    if h is None:
        h = img_height

    x_pad_left = max(0, -x)
    y_pad_left = max(0, -y)

    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(x1 + w - x_pad_left, img_width - x_pad_left)
    y2 = min(y1 + h - y_pad_left, img_height - y_pad_left)
    image = image[y1:y2, x1:x2]

    x_pad = (x_pad_left, w - (x2 - x1) - x_pad_left)
    y_pad = (y_pad_left, h - (y2 - y1) - y_pad_left)
    if x_pad != (0, 0) or y_pad != (0, 0):
        image = np.pad(image, (y_pad, x_pad, (0, 0)))

    return image


def np_save_image(image: np.ndarray, out: str):
    from PIL import Image

    size = (image.shape[1], image.shape[0])
    if len(image.shape) == 2:
        # Grayscale
        Image.frombuffer("L", size, image.tobytes(), "raw", "L", 0, 1).save(out)
    elif image.shape[2] == 3:
        # RGB
        Image.frombuffer(
            "RGB", size, image[:, :, ::-1].tobytes(), "raw", "RGB", 0, 1
        ).save(out)
    else:
        # RGBA
        Image.frombuffer(
            "RGBA", size, image[:, :, [2, 1, 0, 3]].tobytes(), "raw", "RGBA", 0, 1
        ).save(out)


def ensure_np_image(image: "ImageType") -> np.ndarray:
    if isinstance(image, np.ndarray):
        return image

    if image.mode == "RGB":
        image = image.convert("RGBA")

    out = np.array(image)
    out = out[:, :, [2, 1, 0, 3]]  # B G R A
    return out
