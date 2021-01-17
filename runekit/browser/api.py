import base64
import json
import logging
import time
from typing import TYPE_CHECKING, Dict, Callable, List
from urllib.parse import urljoin

from PIL import Image
from PySide2.QtCore import (
    QObject,
    Slot,
    QBuffer,
    QByteArray,
    Property,
    QRect,
    Signal,
    QTimer,
)
from PySide2.QtGui import QGuiApplication, QCursor, QScreen
from PySide2.QtWebChannel import QWebChannel
from PySide2.QtWebEngineCore import QWebEngineUrlSchemeHandler, QWebEngineUrlRequestJob

from runekit.game.instance import WindowPosition
from runekit.image import image_to_bgra

if TYPE_CHECKING:
    from runekit.app.app import App

TRANSFER_LIMIT = 4_000_000


class ApiPermissionDeniedException(Exception):
    required_permission: str

    def __init__(self, required_permission: str):
        super().__init__(
            "Permission '%s' is needed for this action".format(required_permission)
        )
        self.required_permission = required_permission


def _image_to_stream(image: Image, x=0, y=0, width=None, height=None) -> bytes:
    assert image.mode == "RGB" or image.mode == "RGBA"

    if width is None:
        width = image.width
    if height is None:
        height = image.height

    if width * height * 4 > TRANSFER_LIMIT:
        return ""

    return base64.b64encode(image_to_bgra(image, x, y, width, height))


class Alt1Api(QObject):
    app: "App"
    rpc_funcs: Dict[str, Callable]

    _screen_info: QRect
    _bound_regions: List
    _game_position: WindowPosition
    _game_active = False
    _game_last_active = 0

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self._bound_regions = []

        self.rpc_funcs = {
            "getRegion": self.get_region,
            "bindRegion": self.bind_region,
            "bindGetRegion": self.bind_get_region,
        }

        self._update_screen_info()
        gui_app = QGuiApplication.instance()
        gui_app.screenAdded.connect(self.on_screen_update)
        gui_app.screenRemoved.connect(self.on_screen_update)

        self.app.game_instance.on("active", self.on_game_active_change)
        self.app.game_instance.on("resize", self.on_game_resize)
        self.app.game_instance.on("scalingChange", self.on_game_scaling_change)
        self.app.game_instance.on("move", self.on_game_move)
        self._game_position = self.app.game_instance.get_position()
        self._game_active = self.app.game_instance.is_active()

        poll_timer = QTimer(self)
        poll_timer.setInterval(250)

        if self.app.has_permission("gamestate"):
            poll_timer.timeout.connect(self.update_mouse_signal)

        poll_timer.start()

    # region Utils
    def _update_screen_info(self):
        virtual_screen = QRect(0, 0, 0, 0)

        for screen in QGuiApplication.screens():
            geom = screen.virtualGeometry()
            virtual_screen = virtual_screen.united(geom)

        self._screen_info = virtual_screen
        self.screen_update_signal.emit()

    screen_update_signal = Signal()
    # endregion

    # region Qt Properties
    def get_screen_info_x(self):
        return self._screen_info.x()

    screenInfoX = Property(int, get_screen_info_x, notify=screen_update_signal)

    def get_screen_info_y(self):
        return self._screen_info.y()

    screenInfoY = Property(int, get_screen_info_y, notify=screen_update_signal)

    def get_screen_info_width(self):
        return self._screen_info.width()

    screenInfoWidth = Property(int, get_screen_info_width, notify=screen_update_signal)

    def get_screen_info_height(self):
        return self._screen_info.height()

    screenInfoHeight = Property(
        int, get_screen_info_height, notify=screen_update_signal
    )

    def get_capture_interval(self):
        return self.app.game_instance.refresh_rate

    captureInterval = Property(int, get_capture_interval, constant=True)

    def get_mouse_position(self):
        if not self.app.has_permission("gamestate"):
            return 0

        value = QCursor.pos()
        pos = self.app.game_instance.get_position()

        if not QRect(pos.x, pos.y, pos.width, pos.height).contains(value, True):
            # Cursor is out of game
            return 0

        x = value.x() - pos.x
        y = value.y() - pos.y
        return (x << 16) | y

    update_mouse_signal = Signal()
    mousePosition = Property(int, get_mouse_position, notify=update_mouse_signal)

    def get_game_position_x(self):
        return self._game_position.x

    game_moved_signal = Signal()
    gamePositionX = Property(int, get_game_position_x, notify=game_moved_signal)

    def get_game_position_y(self):
        return self._game_position.y

    gamePositionY = Property(int, get_game_position_y, notify=game_moved_signal)

    def get_game_position_width(self):
        return self._game_position.width

    game_resized_signal = Signal()
    gamePositionWidth = Property(
        int, get_game_position_width, notify=game_resized_signal
    )

    def get_game_position_height(self):
        return self._game_position.height

    gamePositionHeight = Property(
        int, get_game_position_height, notify=game_resized_signal
    )

    def get_game_scaling(self):
        return self._game_position.scaling

    game_scaling_change_signal = Signal()
    gameScaling = Property(float, get_game_scaling, notify=game_scaling_change_signal)

    def get_game_active(self):
        return self._game_active

    game_active_change_signal = Signal()
    gameActive = Property(bool, get_game_active, notify=game_active_change_signal)

    def get_game_last_active(self):
        return int(self._game_last_active * 1000)

    gameLastActive = Property(
        int, get_game_last_active, notify=game_active_change_signal
    )
    # endregion

    # region Sync RPC handlers
    def get_region(self, x, y, w, h):
        if not self.app.has_permission("pixel"):
            raise ApiPermissionDeniedException("pixel")

        return _image_to_stream(self.app.game_instance.grab_region(x, y, w, h))

    def bind_region(self, x, y, w, h):
        if not self.app.has_permission("pixel"):
            return 0

        # Alt1 only support one region
        self._bound_regions = [self.app.game_instance.grab_region(x, y, w, h)]
        return 1

    def bind_get_region(self, id, x, y, w, h):
        if not self.app.has_permission("pixel"):
            raise ApiPermissionDeniedException("pixel")

        if id == 0:
            return ""

        try:
            image = self._bound_regions[id - 1]
        except IndexError:
            print("no img index %d" % id)
            return ""

        return _image_to_stream(image, x, y, w, h)

    # endregion

    # region Async RPC handlers (Slots)
    @Slot(str)
    def setTooltip(self, text: str):
        if not self.app.has_permission("overlay"):
            raise ApiPermissionDeniedException("overlay")

        self.app.host.notifier.notify(str(text))

    @Slot(str)
    def identifyAppUrl(self, url):
        """Update app manifest from url"""
        joined_url = urljoin(self.app.absolute_app_url, url)
        # TODO

    @Slot(int, int)
    def setTaskbarProgress(self, type_: int, progress: int):
        if not self.app.has_permission("overlay"):
            raise ApiPermissionDeniedException("overlay")

        type_map = {
            0: "RESET",
            1: "IN_PROGRESS",
            2: "ERROR",
            3: "LOADING",
            4: "PAUSED",
        }
        self.app.game_instance.set_taskbar_progress(type_map[type_], progress)

    # endregion

    # region Event handlers
    @Slot(QScreen)
    def on_screen_update(self, _):
        self._update_screen_info()

    def on_game_active_change(self, active):
        if not active:
            self._game_last_active = time.time()

        self._game_active = active
        self.game_active_change_signal.emit()

    def on_game_resize(self, size):
        self._game_position.width = size[0]
        self._game_position.height = size[1]
        self.game_resized_signal.emit()

    def on_game_scaling_change(self, scale):
        self._game_position.scaling = scale
        self.game_scaling_change_signal.emit()

    def on_game_move(self, pos):
        self._game_position.x = pos[0]
        self._game_position.y = pos[1]
        self.game_moved_signal.emit()

    # endregion


class Alt1WebChannel(QWebChannel):
    app: "App"

    def __init__(self, app: "App", parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.app = app
        self.registerObject("alt1", app.get_api())


class RuneKitSchemeHandler(QWebEngineUrlSchemeHandler):
    api: Alt1Api

    def __init__(self, api: Alt1Api, rpc_secret: bytes, parent=None):
        super().__init__(parent)
        self.api = api
        self.rpc_secret = rpc_secret
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

    def requestStarted(self, req: QWebEngineUrlRequestJob):
        try:
            headers = req.requestHeaders()
            token = headers.get(QByteArray(b"token"))
            if token != self.rpc_secret:
                self.logger.warning("Invalid rpc secret: %s", repr(token))
                req.fail(QWebEngineUrlRequestJob.RequestDenied)
                return

            url = req.requestUrl()
            data = json.loads(url.path())

            func = data["func"]
            del data["func"]
            self.logger.debug("RPC: %s(%s)", func, repr(data))
            out = self.api.rpc_funcs[func](**data)

            body = QBuffer(parent=req)

            if isinstance(out, str):
                body.setData(out.encode("utf-8"))
                req.reply(b"text/plain", body)
            elif isinstance(out, bytes):
                body.setData(out)
                req.reply(b"application/octet-stream", body)
            else:
                body.setData(json.dumps(out).encode("ascii"))
                req.reply(b"application/json", body)
        except:
            req.fail(QWebEngineUrlRequestJob.RequestFailed)
            self.logger.error(
                "Fail to handle request %s", repr(req.requestUrl()), exc_info=True
            )
