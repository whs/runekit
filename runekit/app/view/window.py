import logging
import sys
from typing import Optional

import requests
from PySide2.QtCore import QSize, Qt, QRunnable, Slot, QObject, Signal, QThreadPool
from PySide2.QtGui import QIcon, QPixmap

from runekit.app.view.browser_window import BrowserWindow


class AppWindow(BrowserWindow):
    pool: QThreadPool
    logger: logging.Logger
    app_icon: Optional[QIcon]

    framed = sys.platform != "darwin"

    def __init__(self, **kwargs):
        # TODO: Hide from taskbar/group this as part of one big window?
        flags = Qt.NoDropShadowWindowHint | Qt.WindowStaysOnTopHint

        if self.framed:
            flags |= Qt.CustomizeWindowHint

        super().__init__(flags=flags, **kwargs)
        self.pool = QThreadPool(parent=self)
        self.setWindowTitle(self.app.manifest["appName"])

        self.logger = logging.getLogger(
            __name__
            + "."
            + self.__class__.__name__
            + "."
            + self.app.manifest["appName"]
        )

        self.browser.load(self.app.absolute_app_url)
        self._update_app_icon()

    def _update_app_icon(self):
        if self.app.absolute_icon_url:
            self.logger.debug("Fetching app icon")
            icon_job = IconFetcher(self.app.absolute_icon_url)

            def update_app_icon(icon: QPixmap):
                self.logger.debug("App icon loaded")
                self.app_icon = icon
                self.setWindowIcon(QIcon(icon))

            icon_job.signals.finished.connect(update_app_icon)
            self.pool.start(icon_job)

    def minimumSize(self) -> QSize:
        return QSize(self.app.manifest["minWidth"], self.app.manifest["minHeight"])

    def sizeHint(self) -> QSize:
        return QSize(
            self.app.manifest["defaultWidth"], self.app.manifest["defaultHeight"]
        )

    def maximumSize(self) -> QSize:
        return QSize(self.app.manifest["maxWidth"], self.app.manifest["maxHeight"])


class IconFetcherSignal(QObject):
    finished = Signal(QPixmap)


class IconFetcher(QRunnable):
    def __init__(self, icon_url: str):
        super().__init__()
        self.icon_url = icon_url
        self.signals = IconFetcherSignal()

    @Slot()
    def run(self):
        icon_req = requests.get(self.icon_url)
        icon_req.raise_for_status()
        pixmap = QPixmap()
        pixmap.loadFromData(icon_req.content)
        self.signals.finished.emit(pixmap)
