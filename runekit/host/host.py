from typing import TYPE_CHECKING, List

from PySide2.QtCore import Slot, QCoreApplication
from PySide2.QtWidgets import QMessageBox

from runekit.alt1.schema import AppManifest
from runekit.alt1.utils import fetch_bom_json
from runekit.app import App, AppStore
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

    def on_before_quit(self):
        for app in self.open_app:
            # FIXME: Why app don't cleanup after themselves?
            if app.window:
                app.window.deleteLater()
                app.window = None
            if app.alt1api:
                app.alt1api.deleteLater()
                app.alt1api = None
            if app.web_profile:
                app.web_profile.deleteLater()
                app.web_profile = None

        self.open_app = []

    def launch_app_from_url(self, manifest_url) -> App:
        manifest = fetch_bom_json(manifest_url)
        return self.launch_app(manifest)

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

        self.launch_app(manifest)

    def launch_app(self, manifest: AppManifest):
        instances = self.manager.get_instances()

        if len(instances) == 0:
            QMessageBox.critical(
                None,
                "No game instances found",
                "Cannot find open RuneScape window. Please launch the game before any apps",
            )
            return

        app = App(
            host=self,
            manifest=manifest,
            game_instance=instances[0],
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
