import json
from pathlib import Path
from typing import TypedDict, NamedTuple, List, Optional

from PIL import Image

from runekit.alt1.schema import FontMeta
from ._utils import unblend_known_background

FONT_BASE = Path(__file__).parent / "fonts"


class CharInfo(NamedTuple):
    width: int
    chr: str
    bonus: int
    secondary: bool
    pixels: List[int]


class FontDefinition(TypedDict):
    chars: List[CharInfo]
    width: int
    height: int
    space_width: int
    shadow: bool
    base_y: int
    min_rating: Optional[int]
    max_spaces: Optional[int]


def load_font(name: str) -> FontDefinition:
    meta_file = FONT_BASE / (name + ".fontmeta.json")
    with meta_file.open() as fp:
        meta: FontMeta = json.load(fp)

    return load_font_file(FONT_BASE / (name + ".data.png"), meta)


def load_font_file(image: Path, meta: FontMeta) -> FontDefinition:
    img = Image.open(image)
    return load_font_image(img, meta)


def load_font_image(image: Image, meta: FontMeta) -> FontDefinition:
    if meta["unblendmode"] == "removebg":
        bg_height = int((image.height - 1) / 2)
        background = image.crop((0, bg_height + 1, image.width, image.height))
        font_img = unblend_known_background(
            image.crop((0, 0, image.width, bg_height)),
            background,
            meta["shadow"],
            meta["color"][0],
            meta["color"][1],
            meta["color"][2],
        )
        font_img.show()
    elif meta["unblendmode"] == "raw":
        raise NotImplementedError
    elif meta["unblendmode"] == "blackbg":
        raise NotImplementedError


if __name__ == "__main__":
    load_font("chat_8px")
