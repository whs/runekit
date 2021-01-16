import typing
from typing import TYPE_CHECKING

from PySide2.QtCore import Qt, Slot, QRect
from PySide2.QtGui import QIcon
from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PySide2.QtWidgets import QMainWindow
from runekit.browser import Alt1WebChannel

if TYPE_CHECKING:
    from runekit.app.app import App


class BrowserWindow(QMainWindow):
    app: "App"
    browser: QWebEngineView

    def __init__(self, app: "App", **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self._setup_browser()
        self.setWindowTitle(self.app.manifest["appName"])
        self.setAttribute(Qt.WA_DeleteOnClose)

    def _setup_browser(self):
        self.browser = BrowserView(self)
        self.setCentralWidget(self.browser)

        page = QWebEnginePage(self.app.get_web_profile(), self.browser)
        page.setWebChannel(Alt1WebChannel(app=self.app, parent=self.browser))
        page.geometryChangeRequested.connect(self.on_geometry_change)
        page.iconChanged.connect(self.on_icon_changed)
        page.windowCloseRequested.connect(self.on_window_close)
        self.browser.setPage(page)

    @Slot(QRect)
    def on_geometry_change(self, size: QRect):
        self.resize(size.size())

    @Slot(QIcon)
    def on_icon_changed(self, icon: QIcon):
        self.setWindowIcon(icon)

    @Slot()
    def on_window_close(self):
        self.close()


class BrowserView(QWebEngineView):
    def createWindow(self, type_: QWebEnginePage.WebWindowType) -> QWebEngineView:
        from runekit.app.view.popup_window import PopupWindow

        app_window = typing.cast(BrowserWindow, self.parent())
        popup = PopupWindow(app=app_window.app, parent=app_window)
        popup.setWindowIcon(app_window.windowIcon())
        popup.show()
        return popup.browser
