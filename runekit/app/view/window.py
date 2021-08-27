import logging
import sys
from typing import Optional

from PySide2.QtCore import QSize, Qt, QThreadPool, QSettings
from PySide2.QtGui import QIcon

from runekit.app.view.browser_window import BrowserWindow


class AppWindow(BrowserWindow):
    pool: QThreadPool
    logger: logging.Logger
    app_icon: Optional[QIcon]

    def __init__(self, **kwargs):
        self.settings = QSettings()
        super().__init__(**kwargs)
        self.settings.setParent(self)

        # TODO: Hide from taskbar/group this as part of one big window?
        flags = Qt.NoDropShadowWindowHint | Qt.WindowStaysOnTopHint | Qt.Window
        if self.framed:
            flags |= Qt.CustomizeWindowHint
        self.setWindowFlags(flags)

        self.pool = QThreadPool(parent=self)
        self.setWindowTitle(self.app.manifest["appName"])
        self.snap_to_game()

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

    @property
    def framed(self) -> bool:
        return self.settings.value("settings/styledBorder", "true") == "true" and sys.platform != "darwin"

    def minimumSize(self) -> QSize:
        return QSize(self.app.manifest["minWidth"], self.app.manifest["minHeight"])

    def sizeHint(self) -> QSize:
        return QSize(
            self.app.manifest["defaultWidth"], self.app.manifest["defaultHeight"]
        )

    def maximumSize(self) -> QSize:
        return QSize(self.app.manifest["maxWidth"], self.app.manifest["maxHeight"])
