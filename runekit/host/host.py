import logging
from typing import TYPE_CHECKING, List

from PySide2.QtCore import Slot, QCoreApplication
from PySide2.QtWidgets import QMessageBox

from runekit.alt1.schema import AppManifest
from runekit.alt1.utils import fetch_bom_json
from runekit.app import App, AppStore
from runekit.app.store import app_id
from runekit.host.settings import SettingsDialog
from runekit.ui import AutoNotifier
from runekit.ui.tray import TrayIcon

if TYPE_CHECKING:
    from runekit.game import GameInstance, GameManager


class Host:
    """Host is the root of our application"""

    open_app: List[App]

    def __init__(self, manager: "GameManager"):
        super().__init__()
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.manager = manager
        self.open_app = []
        self.notifier = AutoNotifier()
        self.app_store = AppStore()
        self.tray_icon = TrayIcon(self)
        self.setting_dialog = SettingsDialog(self)
        self.tray_icon.show()

        QCoreApplication.instance().aboutToQuit.connect(self.on_before_quit)
        self.app_store.app_change.connect(self.tray_icon.update_menu)
        self.tray_icon.on_settings.connect(self.open_settings)
        self.manager.instance_removed.connect(self.on_game_quit)

    def on_before_quit(self):
        for app in self.open_app:
            app.close()

    def __del__(self):
        self.open_app = []

    def launch_app_from_url(self, manifest_url) -> App:
        manifest = fetch_bom_json(manifest_url)
        manifest["configUrl"] = manifest_url
        return self.launch_app(app_id(manifest_url), manifest)

    @Slot(str)
    def launch_app_id(self, appid):
        try:
            manifest = self.app_store[appid]
        except KeyError:
            QMessageBox.critical(
                None,
                "App missing",
                "Cannot find application by that ID",
            )
            return

        self.launch_app(appid, manifest)

    def launch_app(self, appid: str, manifest: AppManifest):
        instance = self.manager.get_active_instance()

        if not instance:
            instances = self.manager.get_instances()
            if not instances:
                QMessageBox.critical(
                    None,
                    "No game instances found",
                    "Cannot find open RuneScape window. Please launch the game before any apps",
                )
                return

            instance = instances[0]

        app = App(
            host=self,
            app_id=appid,
            manifest=manifest,
            game_instance=instance,
            source_url=manifest["configUrl"],
        )

        def on_destroy():
            try:
                self.open_app.remove(app)
            except ValueError:
                pass

        window = app.get_window()
        window.show()
        window.destroyed.connect(on_destroy)
        self.open_app.append(app)
        return app

    @Slot()
    def open_settings(self):
        self.setting_dialog.show()
        self.setting_dialog.raise_()

    @Slot()
    def on_game_quit(self, instance: "GameInstance"):
        self.logger.info("Game instance is closing")
        for app in self.open_app[:]:
            if app.game_instance == instance:
                self.logger.debug(
                    "Closing app window %s because instance is closing",
                    app.manifest["appName"],
                )
                app.close()
            self.open_app.remove(app)
