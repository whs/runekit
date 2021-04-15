from typing import TYPE_CHECKING

from PySide2.QtCore import QRect
from PySide2.QtWidgets import QMainWindow

if TYPE_CHECKING:
    from runekit.app import App


class GameSnapMixin(QMainWindow):
    app: "App"
    __last_game_pos: QRect

    def snap_to_game(self):
        rect = self.app.game_instance.get_position()
        pos = rect.topLeft()
        if pos.x() < 0:
            pos.setX(0)
        if pos.y() < 0:
            pos.setY(0)

        self.move(pos)
        self.__last_game_pos = self.app.game_instance.get_position()
        self.app.game_instance.positionChanged.connect(self._update_game_snap)

    def _update_game_snap(self, game_pos: QRect):
        # If the top left spot of us fall into game window, then we move with the game
        tl = self.geometry().topLeft()
        if not game_pos.contains(tl):
            self.__last_game_pos = game_pos
            return

        dx = game_pos.x() - self.__last_game_pos.x()
        dy = game_pos.y() - self.__last_game_pos.y()

        pos = self.pos()
        pos.setX(pos.x() + dx)
        pos.setY(pos.y() + dy)
        self.move(pos)

        self.__last_game_pos = game_pos
