from typing import TYPE_CHECKING

from runekit.alt1.utils import fetch_manifest
from runekit.app import App
from runekit.host.settings import SettingsDialog
from runekit.ui import AutoNotifier

if TYPE_CHECKING:
    from runekit.game import GameInstance


class Host:
    """Host is the root of our application"""

    def __init__(self):
        super().__init__()
        self.notifier = AutoNotifier()

    def start_app(self, manifest_url, instance: "GameInstance") -> App:
        manifest = fetch_manifest(manifest_url)

        app = App(
            host=self,
            manifest=manifest,
            game_instance=instance,
            source_url=manifest_url,
        )
        app.get_window().show()
        return app

    def open_settings(self):
        wnd = SettingsDialog(self)
        wnd.show()
        return wnd
