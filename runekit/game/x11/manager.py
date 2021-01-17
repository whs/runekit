import threading
from typing import List, Dict

from Xlib import X
from Xlib.display import Display
from Xlib.ext import xinput, ge
from Xlib.xobject.drawable import Window

from .instance import GameInstance, X11GameInstance
from runekit.game import GameManager


class X11EventThread(threading.Thread):
    def __init__(self, manager: "X11GameManager", **kwargs):
        super().__init__(name=self.__class__.__name__, **kwargs)
        self.manager = manager
        self.display = manager.display

        self.handlers = {ge.GenericEventCode: self.dispatch_ge}
        self.ge_handlers = {xinput.KeyRelease: self.on_key_release}

    def run(self):
        root = self.display.screen().root
        # root.change_attributes(event_mask=X.PropertyChangeMask | xinput.KeyReleaseMask)
        root.change_attributes(event_mask=xinput.KeyReleaseMask)

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


class X11GameManager(GameManager):
    display: Display

    _instance: Dict[int, GameInstance]

    def __init__(self):
        super().__init__()
        self.display = Display()
        self._instance = {}
        self.event_thread = X11EventThread(self)
        self.event_thread.start()

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

        for index in range(self.display.screen_count()):
            visit(self.display.screen(index).root)

        return out

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
