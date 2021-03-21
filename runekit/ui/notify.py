import abc
from typing import Union

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

    def __init__(self):
        super().__init__()
        self.settings = QSettings(self)
        if (
            QSystemTrayIcon.isSystemTrayAvailable()
            and QSystemTrayIcon.supportsMessages()
        ):
            self.notifier = TrayIconNotifier()
        else:
            self.notifier = TooltipNotifier()

    def notify(self, text):
        self.notifier.notify(text)
