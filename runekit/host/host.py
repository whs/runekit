from typing import TYPE_CHECKING

from PySide2.QtWidgets import QWidget

from runekit.alt1.utils import fetch_manifest
from runekit.app import App

if TYPE_CHECKING:
    from runekit.game import GameInstance


class Host(QWidget):
    """Host map to a game window"""

    def start_app(self, manifest_url, instance: "GameInstance") -> App:
        manifest = fetch_manifest(manifest_url)

        app = App(manifest=manifest, game_instance=instance, source_url=manifest_url)
        app.get_window(parent=self).show()
