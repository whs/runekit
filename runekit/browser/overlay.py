import sys
import collections
import functools
import hashlib
import logging
from typing import List, Dict, Tuple, Optional, TYPE_CHECKING

from PySide2.QtCore import QObject, QTimer, Qt
from PySide2.QtGui import QFont, QPen, QImage, QPixmap
from PySide2.QtWidgets import (
    QGraphicsItem,
    QGraphicsDropShadowEffect,
    QGraphicsTextItem,
    QGraphicsRectItem,
    QGraphicsItemGroup,
    QGraphicsLineItem,
    QGraphicsPixmapItem,
)

from .utils import decode_color

if TYPE_CHECKING:
    from .api import Alt1Api


def barrier(f):
    """Mark f as sync barrier - all preceeding calls must be finished.
    Only affect calls from scheduler"""
    f.barrier = True
    return f


def ensure_overlay(f):
    def out(self: "OverlayApi", *args, **kwargs):
        if not self.overlay_area:
            return

        return f(self, *args, **kwargs)

    return functools.update_wrapper(out, f)


class OverlayApi(QObject):
    # TODO: I think this could be implemented by QGraphicsItemGroup, maybe even more performant
    current_group = ""
    groups: Dict[str, List[QGraphicsItem]]
    frozen_group: Dict[str, QGraphicsItemGroup]
    queue: List[Tuple[int, str, List]]
    last_call_id: Optional[int] = None
    overlay_area: Optional[QGraphicsItem] = None

    def __init__(self, base_api: "Alt1Api", **kwargs):
        super().__init__(**kwargs)
        self.logger = logging.getLogger(__name__)
        self.api = base_api
        self.reset()

        try:
            self.overlay_area = self.api.app.game_instance.get_overlay_area()
        except NotImplementedError:
            pass

    @ensure_overlay
    def enqueue(self, call_id, command, *args):
        # XXX: command is NOT validated. Must be from secure source
        assert command[0] != "_"

        if call_id == 0:
            self.logger.info("Call ID reset")
            self.reset()

        self.queue.append((call_id, command, args))
        self.queue.sort(key=lambda x: x[0])
        # self.logger.debug("%d %s %s", call_id, command, repr(args))

        QTimer.singleShot(0, self.process_queue)

    def process_queue(self):
        while len(self.queue) > 0:
            head = self.queue[0]
            f = getattr(self, head[1])
            if (
                hasattr(f, "barrier")
                and self.last_call_id is not None
                and head[0] != self.last_call_id + 1
            ):
                return

            head = self.queue.pop(0)
            self.last_call_id = head[0]
            try:
                f(*head[2])
            except:
                self.logger.error(
                    "API call exception #%d %s(%s)",
                    head[0],
                    head[1],
                    repr(head[2]),
                    exc_info=True,
                )

    def _finalize_gfx(
        self, gfx: QGraphicsItem, timeout: int, group: Optional[str] = None
    ):
        timeout = min(20000, max(timeout, 1))

        if group is None:
            group = self.current_group

        if group in self.frozen_group:
            self.frozen_group[group].addToGroup(gfx)
        else:
            self.groups[group].append(gfx)
            gfx.setParentItem(self.overlay_area)

        def hide():
            try:
                gfx.scene().removeItem(gfx)
            except AttributeError:
                pass

            try:
                self.groups[group].remove(gfx)
            except (KeyError, ValueError):
                pass

        QTimer.singleShot(timeout, hide)

    def reset(self):
        if hasattr(self, "groups"):
            for item in self.groups.values():
                item.scene().removeItem(item)

        self.groups = collections.defaultdict(list)
        self.frozen_group = {}
        self.queue = []
        self.last_call_id = None

    @barrier
    @ensure_overlay
    def overlay_set_group(self, name: str):
        self.current_group = name

    @barrier
    @ensure_overlay
    def overlay_clear_group(self, name: str):
        for item in self.groups.get(name, []):
            item.scene().removeItem(item)

        try:
            del self.groups[name]
        except KeyError:
            pass

    @barrier
    @ensure_overlay
    def overlay_freeze_group(self, name: str):
        if name in self.frozen_group:
            return

        self.frozen_group[name] = QGraphicsItemGroup()

    @barrier
    @ensure_overlay
    def overlay_continue_group(self, name: str):
        if name not in self.frozen_group:
            return

        gfx = self.frozen_group[name]
        del self.frozen_group[name]
        self._finalize_gfx(gfx, 20000, group=name)

    @barrier
    @ensure_overlay
    def overlay_refresh_group(self, name: str):
        if name not in self.frozen_group:
            return

        self.overlay_continue_group(name)
        self.overlay_freeze_group(name)

    @ensure_overlay
    def overlay_rect(
        self, color: int, x: int, y: int, w: int, h: int, timeout: int, line_width: int
    ):
        pen = QPen(decode_color(color))
        pen.setWidthF(max(1.0, line_width / 10))

        gfx = QGraphicsRectItem(x, y, w, h)
        gfx.setPen(pen)

        self._finalize_gfx(gfx, timeout)

    @ensure_overlay
    def overlay_line(
        self,
        color: int,
        line_width: int,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        timeout: int,
    ):
        pen = QPen(decode_color(color))
        pen.setWidthF(max(1.0, line_width / 10))

        gfx = QGraphicsLineItem(x1, y1, x2, y2)
        gfx.setPen(pen)

        self._finalize_gfx(gfx, timeout)

    @ensure_overlay
    def overlay_text(
        self,
        message: str,
        color: int,
        size: int,
        x: int,
        y: int,
        timeout: int,
        font_name: str,
        centered: bool,
        shadow: bool,
    ):
        gfx = QGraphicsTextItem(message)
        gfx.setDefaultTextColor(decode_color(color))

        if font_name == "" and sys.platform == "darwin":
            # Don't use Helvetica on Mac
            font_name = "Verdana"

        font = QFont(font_name, min(50, size))
        font.setStyleHint(QFont.SansSerif)
        gfx.setFont(font)

        if shadow:
            effect = QGraphicsDropShadowEffect(gfx)
            effect.setBlurRadius(0)
            effect.setColor(Qt.GlobalColor.black)
            effect.setOffset(1, 1)
            gfx.setGraphicsEffect(effect)

        if centered:
            # The provided x, y is at the center of the text
            bound = gfx.boundingRect()
            gfx.setPos(x - (bound.width() / 2), y - (bound.height() / 2))
        else:
            gfx.setPos(x, y)

        self._finalize_gfx(gfx, timeout)

    @ensure_overlay
    def overlay_image(self, img: bytes, x: int, y: int, width: int, timeout: int):
        img = self.get_qimage(img, width)

        gfx = QGraphicsPixmapItem(QPixmap.fromImage(img))
        gfx.setPos(x, y)

        self._finalize_gfx(gfx, timeout)

    @ensure_overlay
    def overlay_set_group_z(self, name: str, z_index: int):
        for item in self.groups.get(name, []):
            item.setZValue(z_index)

    @functools.lru_cache(100)
    def get_qimage(self, img: bytes, width: int):
        height = len(img) / width / 4
        return QImage(img, width, height, QImage.Format_ARGB32)
