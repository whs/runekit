import logging
import sys
from typing import Optional

from PySide2.QtCore import QSize, Qt, QThreadPool
from PySide2.QtGui import QIcon

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

        self.app_icon = self.app.host.app_store.icon(self.app.app_id)
        if self.app_icon:
            self.setWindowIcon(self.app_icon)

    def minimumSize(self) -> QSize:
        return QSize(self.app.manifest["minWidth"], self.app.manifest["minHeight"])

    def sizeHint(self) -> QSize:
        return QSize(
            self.app.manifest["defaultWidth"], self.app.manifest["defaultHeight"]
        )

    def maximumSize(self) -> QSize:
        return QSize(self.app.manifest["maxWidth"], self.app.manifest["maxHeight"])
