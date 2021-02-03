import re
import socket
from typing import Optional
import logging

import psutil
from PySide2.QtCore import QTimer, Slot

logger = logging.getLogger(__name__)


class PsUtilBaseMixin:
    pid: int


class PsUtilNetStat(PsUtilBaseMixin):
    __cached_rdns: dict[str, str]
    __last_world = None
    world_regex = re.compile(r"^world([0-9]+)\.runescape\.com$")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__cached_rdns = {}
        self.__world_timer = QTimer(self)
        self.__world_timer.start(60_000)
        self.__world_timer.timeout.connect(self.__update_world)

    def get_world(self):
        if self.__last_world is None:
            self.__last_world = self.fetch_world()

        return self.__last_world

    def fetch_world(self) -> Optional[int]:
        try:
            addrs = psutil.Process(self.pid).connections()
        except psutil.AccessDenied:
            logger.warning("Cannot get connections", exc_info=True)
            return None

        for conn in addrs:
            if conn.status != psutil.CONN_ESTABLISHED:
                continue

            dns_name = self._rdns(conn.raddr.ip)
            matched_name = self.world_regex.match(dns_name)
            if not matched_name:
                continue

            world = int(matched_name.group(1))
            return world

    @Slot()
    def __update_world(self):
        new_world = self.fetch_world()
        if new_world != self.__last_world:
            self.__last_world = new_world
            self.worldChanged.emit(new_world)

    def _rdns(self, ip: str) -> Optional[str]:
        if ip in self.__cached_rdns:
            return self.__cached_rdns[ip]

        self.__cached_rdns[ip] = socket.getnameinfo((ip, 0), 0)[0]
        return self.__cached_rdns[ip]
