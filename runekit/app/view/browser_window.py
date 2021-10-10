import logging
import sys
from typing import TYPE_CHECKING

from PySide2.QtCore import Qt, Slot, QRect, QObject, QUrl
from PySide2.QtGui import QIcon, QDesktopServices
from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PySide2.QtWidgets import QMainWindow

from runekit.browser import Alt1WebChannel
from runekit.ui.game_snap import GameSnapMixin
from runekit.ui.windowframe import WindowFrame

if TYPE_CHECKING:
    from runekit.app.app import App


class PageClass(QWebEnginePage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

    def javaScriptConsoleMessage(
        self,
        level: QWebEnginePage.JavaScriptConsoleMessageLevel,
        message: str,
        line_no: int,
        src_id: str,
    ):
        logger = self.logger.getChild(self.url().toString())
        log = logger.debug
        if level == QWebEnginePage.InfoMessageLevel:
            log = logger.debug
        elif level == QWebEnginePage.WarningMessageLevel:
            log = logger.warning
        elif level == QWebEnginePage.ErrorMessageLevel:
            log = logger.error
        log("%s", message)

    def acceptNavigationRequest(
        self, url: QUrl, type_: QWebEnginePage.NavigationType, is_main_frame: bool
    ) -> bool:
        if not is_main_frame:
            return super().acceptNavigationRequest(url, type_, is_main_frame)

        # This breaks AFK Warden popups
        # if (
        #     type_ != QWebEnginePage.NavigationTypeTyped
        #     and url.authority() != self.url().authority()
        # ):
        #     # The web is only allowed pages on the same origin
        #     # Cross origin pages would open in browser
        #     if url.scheme() in ("http", "https"):
        #         QDesktopServices.openUrl(url)

        #     return False

        return super().acceptNavigationRequest(url, type_, is_main_frame)


class BrowserWindow(GameSnapMixin, QMainWindow):
    app: "App"
    browser: QWebEngineView
    page_class = PageClass
    framed = False

    def __init__(self, app: "App", **kwargs):
        super().__init__(**kwargs)
        self.app = app

        if self.framed:
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.frame = WindowFrame(parent=self)
            self.frame.on_exit.connect(self.close)
            self.setCentralWidget(self.frame)

        self._setup_browser()
        self.setWindowTitle(self.app.manifest["appName"])
        self.setAttribute(Qt.WA_DeleteOnClose)

    def _setup_browser(self):
        self.browser = BrowserView(self)

        if hasattr(self, "frame"):
            self.frame.set_content(self.browser)
        else:
            self.setCentralWidget(self.browser)

        self.browser.setPage(self.get_page())

    def get_page(self) -> QWebEnginePage:
        page = self.page_class(self.app.get_web_profile(), self.browser)
        page.setWebChannel(Alt1WebChannel(app=self.app, parent=self.browser))
        page.geometryChangeRequested.connect(self.on_geometry_change)
        page.iconChanged.connect(self.on_icon_changed)
        page.windowCloseRequested.connect(self.on_window_close)
        page.featurePermissionRequested.connect(self.on_permission_request)
        return page

    @Slot(QRect)
    def on_geometry_change(self, size: QRect):
        self.resize(size.size())

    @Slot(QIcon)
    def on_icon_changed(self, icon: QIcon):
        self.setWindowIcon(icon)

    @Slot()
    def on_window_close(self):
        self.close()

    @Slot(QUrl, QWebEnginePage.Feature)
    def on_permission_request(self, origin: QUrl, feature: QWebEnginePage.Feature):
        if feature == QWebEnginePage.Notifications and self.app.has_permission(
            "overlay"
        ):
            # FIXME: This doesn't really work - PySide2 doesn't have QWebEngineNotification
            self.browser.page().setFeaturePermission(
                origin, feature, QWebEnginePage.PermissionGrantedByUser
            )
        elif (
            feature in (QWebEnginePage.DesktopVideoCapture, QWebEnginePage.DesktopAudioVideoCapture)
            and self.app.has_permission('pixel')
        ):
            self.browser.page().setFeaturePermission(
                origin, feature, QWebEnginePage.PermissionGrantedByUser
            )
        else:
            self.browser.page().setFeaturePermission(
                origin, feature, QWebEnginePage.PermissionDeniedByUser
            )


class BrowserView(QWebEngineView):
    def createWindow(self, type_: QWebEnginePage.WebWindowType) -> QWebEngineView:
        from runekit.app.view.popup_window import PopupWindow

        app_window = self.browser_window()
        popup = PopupWindow(app=app_window.app, parent=app_window)
        popup.setWindowIcon(app_window.windowIcon())

        def show(ok: bool):
            popup.browser.loadFinished.disconnect(show)
            if ok:
                popup.show()
            else:
                popup.close()

        popup.browser.loadFinished.connect(show)
        return popup.browser

    def browser_window(self) -> BrowserWindow:
        parent: QObject = self.parent()
        while parent is not None:
            if isinstance(parent, BrowserWindow):
                return parent

            parent = parent.parent()
