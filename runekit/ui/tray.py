from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QSystemTrayIcon


class TrayIcon(QSystemTrayIcon):
    def __init__(self):
        global _tray_icon
        super().__init__(QIcon(":/runekit/ui/trayicon.png"))
        _tray_icon = self


def tray_icon() -> TrayIcon:
    return _tray_icon
