import abc
from typing import Union, Dict

from PySide2.QtCore import QObject, QSettings
from PySide2.QtWidgets import QSystemTrayIcon

from .tooltip import TooltipManager
from .tray import tray_icon


class Notifier(abc.ABC):
    @abc.abstractmethod
    def notify(self, text: Union[str, None]):
        ...


class StubNotifier(Notifier):
    def notify(self, text):
        pass


class TooltipNotifier(Notifier):
    def __init__(self):
        self.manager = TooltipManager()

    def notify(self, text):
        self.manager.set_tooltip(text)


class TrayIconNotifier(Notifier):
    def notify(self, text):
        if text:
            tray_icon().showMessage("RuneKit", text)


class AutoNotifier(QObject):
    notifier: Notifier

    METHOD_STUB = 0
    METHOD_NOTIFICATION = 1
    METHOD_TOOLTIP = 2

    def __init__(self):
        super().__init__()
        self.settings = QSettings(self)
        type_ = int(self.settings.value("settings/tooltip", self.METHOD_NOTIFICATION))
        if (
            QSystemTrayIcon.isSystemTrayAvailable()
            and QSystemTrayIcon.supportsMessages()
            and type_ == self.METHOD_NOTIFICATION
        ):
            self.notifier = TrayIconNotifier()
        elif type_ == self.METHOD_TOOLTIP:
            self.notifier = TooltipNotifier()
        else:
            self.notifier = StubNotifier()

    def notify(self, text):
        self.notifier.notify(text)

    @classmethod
    def availableMethods(cls) -> Dict[int, str]:
        out = {
            cls.METHOD_STUB: "Disabled",
            cls.METHOD_TOOLTIP: "Cursor tooltip",
        }
        if (
            QSystemTrayIcon.isSystemTrayAvailable()
            and QSystemTrayIcon.supportsMessages()
        ):
            out[cls.METHOD_NOTIFICATION] = "Notification"

        return out
