import logging
from typing import TYPE_CHECKING, Callable, Tuple, Dict

import numpy as np
from PySide2.QtCore import Qt, QRect, QTimer
from PySide2.QtGui import QGuiApplication, QPen
from PySide2.QtWidgets import (
    QMainWindow,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QGraphicsRectItem,
)

from .qt import qpixmap_to_np
from ..image import is_color_percent_gte

if TYPE_CHECKING:
    from .instance import GameInstance


class DesktopWideOverlay(QMainWindow):
    _instances: Dict[int, QGraphicsItem]
    view: QGraphicsView
    scene: QGraphicsScene

    def __init__(self):
        super().__init__(
            flags=Qt.Widget
            | Qt.FramelessWindowHint
            | Qt.BypassWindowManagerHint
            | Qt.WindowTransparentForInput
            | Qt.WindowStaysOnTopHint
        )
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setStyleSheet("background: transparent")
        self._instances = {}

        virtual_screen = QRect(0, 0, 0, 0)

        for screen in QGuiApplication.screens():
            # TODO: Handle screen change
            geom = screen.virtualGeometry()
            virtual_screen = virtual_screen.united(geom)

        self.scene = QGraphicsScene(
            0, 0, virtual_screen.width(), virtual_screen.height(), parent=self
        )

        self.view = QGraphicsView(self.scene, self)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setStyleSheet("background: transparent")
        self.view.setGeometry(0, 0, virtual_screen.width(), virtual_screen.height())
        self.view.setInteractive(False)

        self.transparent_pen = QPen()
        self.transparent_pen.setBrush(Qt.NoBrush)

        self.setGeometry(virtual_screen)

    def add_instance(
        self, instance: "GameInstance"
    ) -> Tuple[QGraphicsItem, Callable[[], None]]:
        """Add instance to manage, return a disconnect function and the canvas"""
        positionChanged = lambda rect: self.on_instance_moved(instance, rect)
        instance.positionChanged.connect(positionChanged)

        focusChanged = lambda focus: self.on_instance_focus_change(instance, focus)
        instance.focusChanged.connect(focusChanged)

        instance_pos = instance.get_position()
        gfx = QGraphicsRectItem(rect=instance_pos)
        gfx.setPen(self.transparent_pen)
        gfx.setPos(instance_pos.x(), instance_pos.y())
        self.scene.addItem(gfx)
        self._instances[instance.wid] = gfx

        def disconnect():
            gfx.hide()
            self.scene.removeItem(gfx)
            instance.positionChanged.disconnect(positionChanged)
            instance.focusChanged.disconnect(focusChanged)

        return gfx, disconnect

    def on_instance_focus_change(self, instance, focus):
        # self._instances[instance.wid].setVisible(focus)
        pass

    def on_instance_moved(self, instance, pos: QRect):
        rect = self._instances[instance.wid]
        rect.setRect(0, 0, pos.width(), pos.height())
        rect.setPos(pos.x(), pos.y())

    def check_compatibility(self):
        QTimer.singleShot(300, self._check_compatibility)

    def _check_compatibility(self):
        # If we cause black screen then hide ourself out of shame...
        screenshot = QGuiApplication.primaryScreen().grabWindow(0)
        image = qpixmap_to_np(screenshot)
        if is_color_percent_gte(image, color=[0, 0, 0], percent=0.95):
            self.logger.warning("Detected black screen condition. Disabling overlay")
            self.hide()
