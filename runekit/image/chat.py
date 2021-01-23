from typing import List, Tuple, Optional, TypedDict, NamedTuple

from PIL import Image

from runekit.alt1.schema import FontMeta
from ._chat import get_chat_color
from ._utils import rgb, can_blend

Color = Tuple[int, int, int]


class Rectangle(NamedTuple):
    x: int
    y: int
    width: int
    height: int


class OCRLine(NamedTuple):
    text: str
    area: Rectangle


class ChatboxLineFragment(TypedDict):
    color: int
    text: str
    index: int


class ReadCharInfo(NamedTuple):
    chr: str
    base_char: CharInfo
    x: int
    y: int
    score: float
    size_score: float


def read_chatbox_line(
    image: Image,
    x: int,
    y: int,
    colors: List[Color],
    font: FontDefinition,
    backwards=False,
    allow_gap=False,
    budget=15,
    allow_multi_col=True,
):
    colors = [rgb(*x) for x in colors]

    fragment_count = 0
    max_fragment_len = 0
    scan_x = x
    text = ""
    fragments: List[ChatboxLineFragment] = []

    total_space_size = 0
    while True:
        chat_color = get_chat_color(image, (scan_x, y - 8, 6, 8), colors)
        ocr_line = read_chat_line(
            image,
            chat_color,
            font,
            scan_x,
            y,
            backward=backwards and fragment_count == 0,
            forward=True,
            scan_mode=True,
        )

        if not ocr_line or not ocr_line.text or not ocr_line.area[4]:
            if not allow_multi_col and fragment_count != 0:
                break
            if total_space_size >= font["width"] and (
                not allow_gap
                or total_space_size >= 20
                or scan_x - x >= 100
                or budget < 0
            ):
                break

            space_size = font["space_width"]
            if total_space_size != 0 or fragment_count == 0:
                space_size = 1

            scan_x += space_size
            total_space_size += space_size
            budget -= 1
            continue

        if total_space_size >= 2 and ocr_line.text:
            text += " "
            if len(fragments) > 0:
                fragments[-1]["text"] += " "

        coded_color = chat_color[0] * 256 * 256 + chat_color[1] * 256 + chat_color[2]
        fragments.append(
            {
                "color": coded_color,
                "text": ocr_line.text,
                "index": len(text),
            }
        )
        fragment_count += 1
        text += ocr_line.text
        max_fragment_len = max(max_fragment_len, len(ocr_line.text))
        scan_x = max(
            scan_x + font["space_width"], ocr_line.area.x + ocr_line.area.width
        )
        total_space_size = 0

    if len(fragments) == 0 or max_fragment_len <= 2:
        return None

    return {
        "fragments": fragments,
        "text": text,
    }


def read_chat_line(
    image: Image,
    ref_color: Color,
    font: FontDefinition,
    x: int,
    y: int,
    backward=False,
    forward=True,
    scan_mode=False,
) -> Optional[OCRLine]:
    text = ""
    w_fw = x
    w_bw = x

    if forward:
        shift_x = 0
        last_not_found = False
        cur_text = ""
        while True:
            flag2 = scan_mode and not text  # FIXME: What's my name?
            char = read_chat_char(
                image,
                ref_color,
                font,
                x + shift_x,
                y,
                backward=False,
                allow_secondary=not flag2,
            )
            if not char:
                if flag2:
                    backward = False
                    break
                if last_not_found:
                    break

                cur_text += " "
                shift_x += font["space_width"]
                last_not_found = True
            else:
                last_not_found = False
                shift_x += char.base_char["width"]

                if char.base_char.secondary:
                    cur_text += char.chr
                    continue

                text = text + cur_text + char.chr
                cur_text = ""
                w_fw = x + shift_x

    if backward:
        shift_x = 0
        last_not_found = False
        cur_text = ""
        while True:
            char = read_chat_char(image, ref_color, font, x + shift_x, y, backward=True)

            if not char:
                if last_not_found:
                    break
                cur_text = " " + cur_text
                shift_x -= font["space_width"]
                last_not_found = True
                continue

            last_not_found = False
            shift_x -= char.base_char.width
            if char.base_char.secondary:
                cur_text = char.chr + cur_text
                continue
            text = char.chr + cur_text + text
            cur_text = ""
            w_bw = x + shift_x

    return OCRLine(text=text, area=Rectangle(w_bw, y - 9, w_fw - w_bw, 10))


class _chatScore(NamedTuple):
    score: int
    size_score: int
    chr: CharInfo


def read_chat_char(
    image: Image,
    ref_color: Color,
    font: FontDefinition,
    x: int,
    y: int,
    backward=False,
    allow_secondary=True,
) -> Optional[ReadCharInfo]:
    y -= font["base_y"]
    shadow = font["shadow"]

    # Boundary check
    if y < 0 or y + font["height"] >= image.height:
        return None
    if not backward:
        if x < 0 or x + font["width"] > image.width:
            return None
    else:
        if x - font["width"] < 0 or x > image.width:
            return None

    scores: List[_chatScore] = []
    for chr in font["chars"]:
        if chr.secondary and not allow_secondary:
            continue
        if backward:
            chrx = x - chr.width
        else:
            chrx = x

        a = 0
        score = 0
        while a < len(chr.pixels):
            ix = chrx + chr.pixels[a]
            iy = y + chr.pixels[a + 1]
            pixel = image.getpixel((ix, iy))
            if not shadow:
                penalty = can_blend(
                    pixel[0],
                    pixel[1],
                    pixel[2],
                    ref_color[0],
                    ref_color[1],
                    ref_color[2],
                    chr.pixels[a + 2] / 255,
                )
                a += 3
            else:
                lum = chr.pixels[a + 3] / 255
                penalty = can_blend(
                    pixel[0],
                    pixel[1],
                    pixel[2],
                    ref_color[0] * lum,
                    ref_color[1] * lum,
                    ref_color[2] * lum,
                    chr.pixels[a + 2] / 255,
                )
                a += 4

            score += max(0, penalty)

        size_score = score - chr.bonus
        scores.append(_chatScore(score=score, size_score=size_score, chr=chr))

    scores.sort(key=lambda item: item.size_score)

    if not scores:
        return None

    winner = scores[0]
    if winner.score > 400:
        return None

    shift_x = 0
    shift_y = font["base_y"]

    return ReadCharInfo(
        chr=winner.chr.chr,
        base_char=winner.chr,
        x=x + shift_x,
        y=y + shift_y,
        score=winner.score,
        size_score=winner.size_score,
    )
