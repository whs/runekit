import json
import logging
import secrets
from typing import TYPE_CHECKING, Dict, Callable, List
from urllib.parse import urljoin

from PySide2.QtCore import (
    QObject,
    Slot,
    QBuffer,
    QByteArray,
    Property,
    QRect,
    Signal,
    QTimer,
    QThreadPool,
    QRunnable,
    QJsonValue,
)
from PySide2.QtGui import QGuiApplication, QCursor, QScreen
from PySide2.QtWebChannel import QWebChannel
from PySide2.QtWebEngineCore import QWebEngineUrlSchemeHandler, QWebEngineUrlRequestJob

from runekit.browser.overlay import OverlayApi
from runekit.browser.utils import (
    ApiPermissionDeniedException,
    image_to_stream,
    encode_mouse,
)

if TYPE_CHECKING:
    from runekit.app.app import App


class Alt1Api(QObject):
    app: "App"
    rpc_funcs: Dict[str, Callable]

    alt1Signal = Signal(int)

    _screen_info: QRect
    _bound_regions: List
    _game_active = False
    _game_position: QRect
    _game_scaling: float
    _overlay: OverlayApi

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self._bound_regions = []
        self._overlay = OverlayApi(self, parent=self)

        self.rpc_funcs = {
            "getRegion": self.get_region,
            "bindRegion": self.bind_region,
            "bindGetRegion": self.bind_get_region,
        }

        self._update_screen_info()
        self._game_position = self.app.game_instance.get_position()
        self._game_scaling = self.app.game_instance.get_scaling()
        self._private = Alt1ApiPrivate(self, parent=self)
        self.app.game_instance.game_activity.connect(self.game_activity_signal)
        self.app.game_instance.worldChanged.connect(self.world_change_signal)

        poll_timer = QTimer(self)
        poll_timer.setInterval(250)

        if self.app.has_permission("gamestate"):
            poll_timer.timeout.connect(self.mouse_move_signal)

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
        pos = self._game_position

        if not pos.contains(value, True) or not self._game_active:
            # Cursor is out of game
            return 0

        x = value.x() - pos.x()
        y = value.y() - pos.y()
        return encode_mouse(x, y)

    mouse_move_signal = Signal()
    mousePosition = Property(int, get_mouse_position, notify=mouse_move_signal)

    def get_game_position_x(self):
        return self._game_position.x()

    game_position_changed_signal = Signal()
    gamePositionX = Property(
        int, get_game_position_x, notify=game_position_changed_signal
    )

    def get_game_position_y(self):
        return self._game_position.y()

    gamePositionY = Property(
        int, get_game_position_y, notify=game_position_changed_signal
    )

    def get_game_position_width(self):
        return self._game_position.width()

    gamePositionWidth = Property(
        int, get_game_position_width, notify=game_position_changed_signal
    )

    def get_game_position_height(self):
        return self._game_position.height()

    gamePositionHeight = Property(
        int, get_game_position_height, notify=game_position_changed_signal
    )

    def get_game_scaling(self):
        return self._game_scaling

    game_scaling_change_signal = Signal()
    gameScaling = Property(float, get_game_scaling, notify=game_scaling_change_signal)

    def get_game_active(self):
        return self._game_active

    game_active_change_signal = Signal()
    gameActive = Property(bool, get_game_active, notify=game_active_change_signal)

    game_activity_signal = Signal()

    def get_world(self):
        return self.app.game_instance.get_world()

    world_change_signal = Signal()
    world = Property(bool, get_world, notify=world_change_signal)
    # endregion

    # region Sync RPC handlers
    def get_region(self, x, y, w, h):
        if not self.app.has_permission("pixel"):
            raise ApiPermissionDeniedException("pixel")

        return image_to_stream(self.app.game_instance.grab_region(x, y, w, h))

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

        return image_to_stream(image, x, y, w, h)

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

    @Slot(QJsonValue, QJsonValue)
    def setTaskbarProgress(self, type_: QJsonValue, progress: QJsonValue):
        if not self.app.has_permission("overlay"):
            raise ApiPermissionDeniedException("overlay")

        type_map = {
            0: "RESET",
            1: "IN_PROGRESS",
            2: "ERROR",
            3: "LOADING",
            4: "PAUSED",
        }
        # This can be called with null, but since the default value is 0 we call RESET anyway
        self.app.game_instance.set_taskbar_progress(
            type_map[type_.toDouble(0)], progress.toDouble(0)
        )

    @Slot(int, int, int, int, int, int, int, int)
    def overlayRect(self, call_id, color, x, y, w, h, time, line_width):
        if not self.app.has_permission("overlay"):
            raise ApiPermissionDeniedException("overlay")

        self._overlay.enqueue(
            call_id, "overlay_rect", color, x, y, w, h, time, line_width
        )

    @Slot(int, str, int, int, int, int, int, str, bool, bool)
    def overlayTextEx(
        self, call_id, message, color, size, x, y, timeout, font_name, centered, shadow
    ):
        if not self.app.has_permission("overlay"):
            raise ApiPermissionDeniedException("overlay")

        self._overlay.enqueue(
            call_id,
            "overlay_text",
            message,
            color,
            size,
            x,
            y,
            timeout,
            font_name,
            centered,
            shadow,
        )

    @Slot(int, str)
    def overlaySetGroup(self, call_id, name):
        if not self.app.has_permission("overlay"):
            raise ApiPermissionDeniedException("overlay")

        self._overlay.enqueue(call_id, "overlay_set_group", name)

    @Slot(int, str)
    def overlayClearGroup(self, call_id, name):
        if not self.app.has_permission("overlay"):
            raise ApiPermissionDeniedException("overlay")

        self._overlay.enqueue(call_id, "overlay_clear_group", name)

    @Slot(int, str, int)
    def overlaySetGroupZIndex(self, call_id, group, zIndex):
        if not self.app.has_permission("overlay"):
            raise ApiPermissionDeniedException("overlay")

        self._overlay.enqueue(call_id, "overlay_set_group_z", group, zIndex)

    # endregion


class Alt1ApiPrivate(QObject):
    """Alt1Api private parts that cannot be called from the web """

    api: Alt1Api

    def __init__(self, api, **kwargs):
        super().__init__(**kwargs)
        self.api = api

        gui_app = QGuiApplication.instance()

        gui_app.screenAdded.connect(self.on_screen_update)
        gui_app.screenRemoved.connect(self.on_screen_update)

        self.api.app.game_instance.focusChanged.connect(self.on_game_active_change)
        self.api.app.game_instance.positionChanged.connect(self.on_game_position_change)
        self.api.app.game_instance.scalingChanged.connect(self.on_game_scaling_change)
        self.api.app.game_instance.alt1_pressed.connect(self.on_alt1)

    @Slot(QScreen)
    def on_screen_update(self, _):
        self.api._update_screen_info()

    @Slot(bool)
    def on_game_active_change(self, active):
        self.api._game_active = active
        self.api.game_active_change_signal.emit()

    @Slot(QRect)
    def on_game_position_change(self, pos):
        self.api._game_position = pos
        self.api.game_position_changed_signal.emit()

    @Slot(float)
    def on_game_scaling_change(self, scale):
        self.api._game_scaling = scale
        self.api.game_scaling_change_signal.emit()

    @Slot()
    def on_alt1(self):
        mouse = self.api.get_mouse_position()
        self.api.alt1Signal.emit(mouse)


class Alt1WebChannel(QWebChannel):
    app: "App"

    def __init__(self, app: "App", parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)
        self.app = app
        self.registerObject("alt1", app.get_api())


class RuneKitRequestProcessSignals(QObject):
    successSignal = Signal(QWebEngineUrlRequestJob, bytes, bytes)


class RuneKitRequestProcess(QRunnable):
    def __init__(
        self,
        handler: "RuneKitSchemeHandler",
        request: QWebEngineUrlRequestJob,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.handler = handler
        self.request = request
        self.signals = RuneKitRequestProcessSignals(parent=self.request)

    def run(self):
        try:
            url = self.request.requestUrl()
            data = json.loads(url.path())

            func = data["func"]
            del data["func"]
            self.handler.logger.debug("RPC: %s(%s)", func, repr(data))

            out = self.handler.api.rpc_funcs[func](**data)

            if isinstance(out, str):
                self.signals.successSignal.emit(
                    self.request, b"text/plain", out.encode("utf-8")
                )
            elif isinstance(out, bytes):
                self.signals.successSignal.emit(
                    self.request, b"application/octet-stream", out
                )
            else:
                self.signals.successSignal.emit(
                    self.request, b"application/json", json.dumps(out).encode("ascii")
                )
        except:
            self.request.fail(QWebEngineUrlRequestJob.RequestFailed)
            self.handler.logger.error(
                "Fail to handle request %s",
                repr(self.request.requestUrl()),
                exc_info=True,
            )


class RuneKitSchemeHandler(QWebEngineUrlSchemeHandler):
    api: Alt1Api

    def __init__(self, api: Alt1Api, rpc_secret: bytes, parent=None):
        super().__init__(parent)
        self.api = api
        self.rpc_secret = rpc_secret
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.thread_pool = QThreadPool(parent=self)

    def requestStarted(self, req: QWebEngineUrlRequestJob):
        headers = req.requestHeaders()
        token = headers.get(QByteArray(b"token"))
        if not secrets.compare_digest(token, self.rpc_secret):
            self.logger.warning("Invalid rpc secret: %s", repr(token))
            req.fail(QWebEngineUrlRequestJob.RequestDenied)
            return

        processor = RuneKitRequestProcess(self, req, parent=req)
        processor.signals.successSignal.connect(self.on_success)
        if "overLay" in req.requestUrl().path():
            # FIXME: RuneKitRequestProcess should be able to notify main thread that
            # this should run in main thread

            # Overlay functions require main thread
            processor.run()
        else:
            self.thread_pool.start(processor)

    @Slot(QWebEngineUrlRequestJob, bytes, bytes)
    def on_success(self, request, content_type, reply):
        body = QBuffer(parent=request)
        body.setData(reply)
        request.reply(content_type, body)
