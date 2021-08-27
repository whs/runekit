import time
from functools import reduce
from typing import List, Dict, Optional, Union

import Quartz
import ApplicationServices
from PySide2.QtCore import QTimer, Signal, Slot
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import QMessageBox

from .instance import QuartzGameInstance
from runekit.game.overlay import DesktopWideOverlay
from ..instance import GameInstance
from ..manager import GameManager

has_prompted_accessibility = False


class QuartzGameManager(GameManager):
    _instances: Dict[int, GameInstance]
    overlay: DesktopWideOverlay

    request_accessibility_popup = Signal()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._instances = {}
        self.request_accessibility_popup.connect(self.accessibility_popup)
        self._setup_tap()

        ApplicationServices.AXIsProcessTrustedWithOptions(
            {
                ApplicationServices.kAXTrustedCheckOptionPrompt: True,
            }
        )
        while not ApplicationServices.AXIsProcessTrusted():
            time.sleep(0.1)

        self._setup_overlay()

    def _setup_tap(self):
        events = [
            Quartz.kCGEventLeftMouseDown,
            Quartz.kCGEventRightMouseDown,
            Quartz.kCGEventKeyDown,
        ]
        events = [Quartz.CGEventMaskBit(e) for e in events]
        event_mask = reduce(lambda a, b: a | b, events)
        self._tap = Quartz.CGEventTapCreate(
            Quartz.kCGAnnotatedSessionEventTap,
            Quartz.kCGTailAppendEventTap,
            Quartz.kCGEventTapOptionListenOnly,  # TODO: Tap keydown synchronously
            event_mask,
            self._on_input,
            None,
        )
        source = Quartz.CFMachPortCreateRunLoopSource(None, self._tap, 0)
        Quartz.CFRunLoopAddSource(
            Quartz.CFRunLoopGetCurrent(), source, Quartz.kCFRunLoopCommonModes
        )

    def _setup_overlay(self):
        self.overlay = DesktopWideOverlay()

        def start():
            self.overlay.show()
            self.overlay.check_compatibility()

        # Seems like QGraphicsView has a delay before applying stylesheet
        # Put some delay to allow it to initialize and not flash
        QTimer.singleShot(1000, start)

    def stop(self):
        try:
            self.overlay.hide()
            self.overlay.deleteLater()
        except RuntimeError:
            pass

    def get_instances(self) -> List[GameInstance]:
        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID
        )

        for window in windows:
            if window[Quartz.kCGWindowOwnerName] == "rs2client":
                wid = int(window[Quartz.kCGWindowNumber])
                if wid not in self._instances:
                    pid = int(window[Quartz.kCGWindowOwnerPID])
                    self._instances[wid] = QuartzGameInstance(
                        self, wid, pid, parent=self
                    )

        return list(self._instances.values())

    def get_active_instance(self) -> Union[GameInstance, None]:
        if not self._instances:
            return None

        return list(self._instances.values())[0]

    def get_instance_by_pid(self, pid: int) -> Optional[QuartzGameInstance]:
        for instance in self._instances.values():
            if instance.pid == pid:
                return instance

    def _on_input(self, proxy, type_, event, _):
        event_type = Quartz.CGEventGetType(event)
        if event_type == Quartz.kCGEventTapDisabledByUserInput:
            QTimer.singleShot(0, self.accessibility_popup)
            return event
        elif event_type == Quartz.kCGEventTapDisabledByTimeout:
            Quartz.CGEventTapEnable(self._tap, True)
            return event

        nsevent = Quartz.NSEvent.eventWithCGEvent_(event)
        if nsevent.type() == Quartz.NSEventTypeKeyDown:
            front_app = Quartz.NSWorkspace.sharedWorkspace().frontmostApplication()
            instance = self.get_instance_by_pid(front_app.processIdentifier())
        else:
            instance = self._instances.get(nsevent.windowNumber())

        if not instance:
            return event

        # Check for cmd1
        if nsevent.type() == Quartz.NSEventTypeKeyDown:
            if (
                nsevent.keyCode() == 18
                and nsevent.modifierFlags() & Quartz.NSEventModifierFlagCommand
            ):
                instance.alt1_pressed.emit()
                return None

        instance.game_activity.emit()

        return event

    @Slot()
    def accessibility_popup(self):
        global has_prompted_accessibility
        if has_prompted_accessibility:
            return

        has_prompted_accessibility = True
        msgbox = QMessageBox(
            QMessageBox.Warning,
            "Permission required",
            "RuneKit needs Screen Recording permission\n\nOpen System Preferences > Security > Privacy > Screen Recording to allow this",
            QMessageBox.Open | QMessageBox.Ignore,
        )
        button = msgbox.exec()

        if button == QMessageBox.Open:
            QDesktopServices.openUrl(
                "x-apple.systempreferences:com.apple.preference.security?Privacy_Screen Recording"
            )
