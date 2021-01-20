import logging
from typing import List, Dict

from PySide2.QtCore import QThread, Slot, Signal, QObject
from Xlib import X
from Xlib.display import Display
from Xlib.ext import xinput, ge
from Xlib.protocol import event
from Xlib.xobject.drawable import Window
import Xlib.threaded

from runekit.game import GameManager
from .instance import GameInstance, X11GameInstance


class X11EventWorker(QObject):
    on_active_window_changed = Signal(int)
    on_alt1 = Signal(int)

    def __init__(self, manager: "X11GameManager", **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.display = manager.display
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

        self.handlers = {
            ge.GenericEventCode: self.dispatch_ge,
            X.PropertyNotify: self.on_property_change,
        }
        self.ge_handlers = {xinput.KeyPress: self.on_key_press}
        self.active_win_id = self.manager.get_active_window()

        self._NET_ACTIVE_WINDOW = self.display.get_atom("_NET_ACTIVE_WINDOW")

    @Slot()
    def run(self):
        root = self.display.screen().root
        root.change_attributes(event_mask=X.PropertyChangeMask)

        while True:
            evt = self.display.next_event()
            if evt.send_event != 0:
                continue

            try:
                handler = self.handlers.get(evt.type)
                if handler:
                    handler(evt)
            except:
                self.logger.error("Error handling event %s", repr(evt), exc_info=True)
                continue

    def dispatch_ge(self, evt: ge.GenericEvent):
        handler = self.ge_handlers.get(evt.evtype)
        if handler:
            handler(evt)

    def on_key_press(self, evt):
        window = evt.data.event
        # alt1
        if evt.data.mods.effective_mods & X.Mod1Mask and evt.data.detail == 10:
            self.on_alt1.emit(window.id)
            self.logger.debug("alt1 pressed %s", repr(evt))

        window.xinput_ungrab_keycode(evt.data.deviceid, evt.data.detail, (X.Mod1Mask,))
        self.manager._setup_grab(window)

    def on_property_change(self, evt: event.PropertyNotify):
        if evt.atom == self._NET_ACTIVE_WINDOW:
            active_win_id = self.manager.get_active_window()

            if self.active_win_id == active_win_id:
                return

            self.active_win_id = active_win_id
            self.logger.debug(
                "Active window changed to %d - %s", active_win_id, repr(evt)
            )
            self.on_active_window_changed.emit(active_win_id)


class X11GameManager(GameManager):
    display: Display

    _instance: Dict[int, X11GameInstance]

    def __init__(self, **kwargs):
        super().__init__(*kwargs)
        self.display = Display()
        self._NET_ACTIVE_WINDOW = self.display.get_atom("_NET_ACTIVE_WINDOW")
        self._instance = {}

        self.event_thread = QThread()

        self.event_worker = X11EventWorker(self)
        self.event_worker.moveToThread(self.event_thread)
        self.event_thread.started.connect(self.event_worker.run)
        self.event_worker.on_active_window_changed.connect(
            self.on_active_window_changed
        )
        self.event_worker.on_alt1.connect(self.on_alt1)

        self.event_thread.start()

    def get_instances(self) -> List[GameInstance]:
        def visit(window):
            try:
                wm_class = window.get_wm_class()
            except:
                return

            if wm_class and wm_class[0] == "RuneScape":
                if window.id not in self._instance:
                    instance = X11GameInstance(self, window, parent=self)
                    self._setup_grab(window)
                    self._instance[window.id] = instance

            for child in window.query_tree().children:
                visit(child)

        visit(self.display.screen().root)

        return list(self._instance.values())

    def _setup_grab(self, window: Window):
        # alt1
        window.xinput_grab_keycode(
            xinput.AllDevices,
            X.CurrentTime,
            10,
            xinput.GrabModeAsync,
            xinput.GrabModeAsync,
            True,
            xinput.KeyPressMask,
            (X.Mod1Mask,),
        )

    def get_active_window(self) -> int:
        resp = self.display.screen().root.get_full_property(
            self._NET_ACTIVE_WINDOW, X.AnyPropertyType
        )
        return resp.value[0]

    @Slot(int)
    def on_active_window_changed(self, winid):
        for id_, instance in self._instance.items():
            active = winid == id_

            if active != instance._is_active:
                instance.activeChanged.emit(active)

            instance._is_active = active

    @Slot(int)
    def on_alt1(self, winid):
        if winid in self._instance:
            self._instance[winid].alt1_pressed.emit()
