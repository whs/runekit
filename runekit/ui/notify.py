import abc
from typing import Union

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QSystemTrayIcon

from .tooltip import TooltipManager


class Notifier(abc.ABC):
    @abc.abstractmethod
    def notify(self, text: Union[str, None]):
        ...


class TooltipNotifier(Notifier):
    def __init__(self):
        self.manager = TooltipManager()

    def notify(self, text):
        self.manager.set_tooltip(text)


class TrayIconNotifier(Notifier):
    def __init__(self):
        self.icon = QSystemTrayIcon(QIcon(":/runekit/ui/trayicon.png"))
        self.icon.show()

    def notify(self, text):
        if text:
            self.icon.showMessage("RuneKit", text)


class AutoNotifier(Notifier):
    notifier: Notifier

    def __init__(self):
        if (
            QSystemTrayIcon.isSystemTrayAvailable()
            and QSystemTrayIcon.supportsMessages()
        ):
            self.notifier = TrayIconNotifier()
        else:
            self.notifier = TooltipNotifier()

    def notify(self, text):
        self.notifier.notify(text)
