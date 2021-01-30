import logging
import sys
from typing import List, Dict, Tuple

from PySide2.QtCore import QThread, Slot, Signal, QObject
import xcffib
import xcffib.xproto
import xcffib.composite
import xcffib.shm
import xcffib.xinput
import sysv_ipc

from runekit.game import GameManager
from .instance import GameInstance, X11GameInstance
from . import ge
from .utils import ClassDict

MAX_SHM = 10
NET_ACTIVE_WINDOW = "_NET_ACTIVE_WINDOW"


class X11GameManager(GameManager):
    connection: xcffib.Connection

    _instance: Dict[int, X11GameInstance]
    _atom: Dict[bytes, int]
    _shm: List[Tuple[int, sysv_ipc.SharedMemory]]

    def __init__(self, **kwargs):
        super().__init__(*kwargs)
        self._instance = {}
        self._atom = {}
        self._shm = []

        self.connection = xcffib.Connection()
        self.screen = self.connection.get_screen_pointers()[self.connection.pref_screen]
        self.xcomposite = self.connection(xcffib.composite.key)
        self.xshm = self.connection(xcffib.shm.key)
        self.xinput = self.connection(xcffib.xinput.key)
        self._setup_composite()

        self.event_thread = QThread()

        self.event_worker = X11EventWorker(self)
        self.event_worker.moveToThread(self.event_thread)
        self.event_thread.started.connect(self.event_worker.run)
        self.event_thread.finished.connect(self.event_worker.deleteLater)
        self.event_worker.on_active_window_changed.connect(
            self.on_active_window_changed
        )

        self.event_thread.start()

    def get_instances(self) -> List[GameInstance]:
        def visit(wid: int):
            wm_class = self.get_property(wid, xcffib.xproto.Atom.WM_CLASS)

            if wm_class:
                instance_name, app_name = wm_class.split("\00")
                if app_name == "RuneScape":
                    if wid not in self._instance:
                        instance = X11GameInstance(self, wid, parent=self)
                        self._instance[wid] = instance

                    return

            query = self.connection.core.QueryTree(wid).reply()
            for child in query.children:
                visit(child)

        visit(self.screen.root)

        return list(self._instance.values())

    def get_active_window(self) -> int:
        return self.get_property(self.screen.root, "_NET_ACTIVE_WINDOW")

    @Slot(int)
    def on_active_window_changed(self, winid):
        for id_, instance in self._instance.items():
            active = winid == id_

            if active != instance.is_focused:
                instance.is_focused = active
                instance.focusChanged.emit(active)

    def _setup_composite(self):
        self.xcomposite.QueryVersion(0, 4, is_checked=True)

    def get_property(
        self,
        wid: int,
        name: str,
        type_=xcffib.xproto.GetPropertyType.Any,
        index=0,
        max_values=1000,
    ):
        reply = self.connection.core.GetProperty(
            False,
            wid,
            self.get_atom(name),
            type_,
            index,
            max_values,
        ).reply()

        if reply.type == xcffib.xproto.Atom.STRING:
            return reply.value.to_string()[:-1]
        elif reply.type == xcffib.xproto.Atom.WINDOW:
            return int.from_bytes(reply.value.buf(), byteorder=sys.byteorder)

        return reply.value

    def get_atom(self, atom: str) -> int:
        if isinstance(atom, int):
            return atom

        if hasattr(xcffib.xproto.Atom, atom):
            return getattr(xcffib.xproto.Atom, atom)

        atom = atom.encode("ascii")

        if atom in self._atom:
            return self._atom[atom]

        out = self.connection.core.InternAtom(False, len(atom), atom).reply().atom
        self._atom[atom] = out

        return out

    def get_shm(self, size: int) -> Tuple[int, sysv_ipc.SharedMemory]:
        for item in self._shm:
            if item[1].size >= size:
                self._shm.remove(item)
                return item

        shm = sysv_ipc.SharedMemory(None, flags=sysv_ipc.IPC_CREX, size=size)
        xid = self.connection.generate_id()
        self.xshm.Attach(xid, shm.id, False, is_checked=True)
        return xid, shm

    def free_shm(self, shm: Tuple[int, sysv_ipc.SharedMemory]):
        self._shm.append(shm)
        self.gc_shm()

    def gc_shm(self):
        while len(self._shm) > MAX_SHM:
            xid, shm = self._shm.pop(0)
            self.xshm.Detach(xid)
            shm.detach()
            shm.remove()


class X11EventWorker(QObject):
    on_active_window_changed = Signal(int)
    stop = False

    def __init__(self, manager: "X11GameManager", **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

        self.handlers = ClassDict(
            {
                xcffib.xproto.PropertyNotifyEvent: self.on_property_change,
                xcffib.xinput.KeyPressEvent: self.on_key_press,
                xcffib.xinput.KeyReleaseEvent: self.on_key_press,
            }
        )
        self.active_win_id = self.manager.get_active_window()

    @Slot()
    def run(self):
        self.manager.connection.core.ChangeWindowAttributes(
            self.manager.screen.root,
            xcffib.xproto.CW.EventMask,
            [xcffib.xproto.EventMask.PropertyChange],
            is_checked=True,
        )

        while True:
            if self.stop:
                self.logger.debug("Exiting")
                return

            evt = self.manager.connection.wait_for_event()

            if isinstance(evt, ge.GeGenericEvent):
                evt = evt.to_event(self.manager.connection)

            try:
                handler = self.handlers[evt]
            except KeyError:
                self.logger.debug("Unhandled event %s", repr(evt))
                continue

            try:
                handler(evt)
            except:
                self.logger.error("Error handling event %s", repr(evt), exc_info=True)

    def on_key_press(self, evt: xcffib.xinput.KeyPressEvent):
        print(
            {
                "deviceid": evt.deviceid,
                "time": evt.time,
                "detail": evt.detail,
                "root": evt.root,
                "event": evt.event,
                "child": evt.child,
                "root_x": evt.root_x,
                "root_y": evt.root_y,
                "event_x": evt.event_x,
                "event_y": evt.event_y,
                "buttons_len": evt.buttons_len,
                "valuators_len": evt.valuators_len,
                "sourceid": evt.sourceid,
                "flags": evt.flags,
            }
        )
        try:
            instance = self.manager._instance[evt.root]
        except KeyError:
            self.logger.debug(
                "Unknown KeyPressEvent to instance %s: %s", evt.root, repr(evt)
            )
            self.manager.xinput.XIPassiveUngrabDevice(
                evt.root,
                evt.detail,
                evt.deviceid,
                1,
                xcffib.xinput.GrabType.Keycode,
                evt.mods.effective,
            )
            return

        instance.key_press.emit(evt)

    def on_property_change(self, evt: xcffib.xproto.PropertyNotifyEvent):
        if evt.atom == self.manager.get_atom(NET_ACTIVE_WINDOW):
            active_win_id = self.manager.get_active_window()

            if self.active_win_id == active_win_id:
                return

            self.active_win_id = active_win_id
            self.logger.debug(
                "Active window changed to %d - %s", active_win_id, repr(evt)
            )
            self.on_active_window_changed.emit(active_win_id)
