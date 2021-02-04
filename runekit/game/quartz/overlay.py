from typing import TYPE_CHECKING, Callable, Tuple, Dict

from PySide2.QtCore import Qt, QRect
from PySide2.QtGui import QGuiApplication, QPen
from PySide2.QtWidgets import QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsTextItem, \
    QGraphicsRectItem

if TYPE_CHECKING:
    from .instance import QuartzGameInstance

class QuartzOverlay(QMainWindow):
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
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._instances = {}

        virtual_screen = QRect(0, 0, 0, 0)

        for screen in QGuiApplication.screens():
            # TODO: Handle screen change
            geom = screen.virtualGeometry()
            virtual_screen = virtual_screen.united(geom)

        self.scene = QGraphicsScene(0, 0, virtual_screen.width(), virtual_screen.height(), parent=self)

        self.view = QGraphicsView(self.scene, self)
        self.view.setStyleSheet("background: transparent")
        self.view.setGeometry(0, 0, virtual_screen.width(), virtual_screen.height())
        self.view.setInteractive(False)

        self.transparent_pen = QPen()
        self.transparent_pen.setBrush(Qt.NoBrush)

        self.setGeometry(virtual_screen)

    def add_instance(self, instance: 'QuartzGameInstance') -> Tuple[QGraphicsItem, Callable[[], None]]:
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
            instance.positionChanged.disconnect(positionChanged)
            instance.focusChanged.disconnect(focusChanged)
            gfx.hide()
            self.scene.removeItem(gfx)

        return gfx, disconnect

    def on_instance_focus_change(self, instance, focus):
        # self._instances[instance.wid].setVisible(focus)
        pass

    def on_instance_moved(self, instance, pos: QRect):
        rect = self._instances[instance.wid]
        rect.setRect(0, 0, pos.width(), pos.height())
        rect.setPos(pos.x(), pos.y())
