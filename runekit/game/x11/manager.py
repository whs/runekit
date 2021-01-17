import threading
from typing import List, Dict

from Xlib import X
from Xlib.display import Display
from Xlib.ext import xinput, ge
from Xlib.protocol import event
from Xlib.xobject.drawable import Window

from .instance import GameInstance, X11GameInstance
from runekit.game import GameManager


class X11EventThread(threading.Thread):
    def __init__(self, manager: "X11GameManager", **kwargs):
        super().__init__(name=self.__class__.__name__, **kwargs)
        self.manager = manager
        self.display = manager.display

        self.handlers = {
            ge.GenericEventCode: self.dispatch_ge,
            X.PropertyNotify: self.on_property_change,
        }
        self.ge_handlers = {xinput.KeyRelease: self.on_key_release}
        self.active_win_id = self.manager.get_active_window()

        self._NET_ACTIVE_WINDOW = self.display.get_atom("_NET_ACTIVE_WINDOW")

    def run(self):
        root = self.display.screen().root
        root.change_attributes(event_mask=X.PropertyChangeMask)

        while True:
            evt = self.display.next_event()
            if evt.send_event != 0:
                continue

            handler = self.handlers.get(evt.type)
            if handler:
                handler(evt)

    def dispatch_ge(self, evt: ge.GenericEvent):
        handler = self.ge_handlers.get(evt.evtype)
        if handler:
            handler(evt)

    def on_key_release(self, evt):
        # alt1
        if evt.data.mods.effective_mods & X.Mod1Mask and evt.data.detail == 10:
            self.manager.emit("alt1")

    def on_property_change(self, evt: event.PropertyNotify):
        if evt.atom == self._NET_ACTIVE_WINDOW:
            active_win_id = self.manager.get_active_window()

            if self.active_win_id == active_win_id:
                return

            self.active_win_id = active_win_id
            self.manager.emit("active")


class X11GameManager(GameManager):
    display: Display

    _instance: Dict[int, GameInstance]

    def __init__(self):
        super().__init__()
        self.display = Display()
        self._NET_ACTIVE_WINDOW = self.display.get_atom("_NET_ACTIVE_WINDOW")
        self._instance = {}
        self.event_thread = X11EventThread(self)
        self.event_thread.start()
        self.on("active", self.broadcast_active)

    def get_instances(self) -> List[GameInstance]:
        out = []

        def visit(window):
            try:
                wm_class = window.get_wm_class()
            except:
                return

            if wm_class and wm_class[0] == "RuneScape":
                if window.id not in self._instance:
                    self.prepare_window(window)
                    self._instance[window.id] = X11GameInstance(self, window)
                out.append(self._instance[window.id])

            for child in window.query_tree().children:
                visit(child)

        visit(self.display.screen().root)

        return out

    def get_active_window(self) -> int:
        resp = self.display.screen().root.get_full_property(
            self._NET_ACTIVE_WINDOW, X.AnyPropertyType
        )
        return resp.value[0]

    def prepare_window(self, window: Window):
        # alt1
        window.xinput_grab_keycode(
            xinput.AllDevices,
            X.CurrentTime,
            10,
            xinput.GrabModeAsync,
            xinput.GrabModeAsync,
            True,
            xinput.KeyReleaseMask,
            (X.Mod1Mask,),
        )

    def broadcast_active(self):
        active_winid = self.get_active_window()
        for id_, instance in self._instance.items():
            instance.emit("active", active_winid == id_)
