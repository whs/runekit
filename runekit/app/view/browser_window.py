from typing import TYPE_CHECKING

from PySide2.QtCore import Qt, Slot, QRect, QObject, Signal, QEvent
from PySide2.QtGui import QIcon, QCloseEvent
from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PySide2.QtWidgets import QMainWindow

from runekit.browser import Alt1WebChannel
from runekit.ui.windowframe import WindowFrame

if TYPE_CHECKING:
    from runekit.app.app import App


class BrowserWindow(QMainWindow):
    app: "App"
    browser: QWebEngineView
    framed = False

    def __init__(self, app: "App", **kwargs):
        super().__init__(**kwargs)
        self.app = app

        if self.framed:
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

        app_window = self.browser_window()
        popup = PopupWindow(app=app_window.app, parent=app_window)
        popup.setWindowIcon(app_window.windowIcon())
        popup.show()
        return popup.browser

    def browser_window(self) -> BrowserWindow:
        parent: QObject = self.parent()
        while parent is not None:
            if isinstance(parent, BrowserWindow):
                return parent

            parent = parent.parent()
