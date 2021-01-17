from typing import Optional, TYPE_CHECKING, List
from urllib.parse import urljoin

from PySide2.QtCore import Qt

from runekit.alt1.schema import AppManifest
from runekit.app.view.window import AppWindow
from runekit.browser import Alt1Api, WebProfile

if TYPE_CHECKING:
    from runekit.game import GameInstance
    from runekit.host import Host


class App:
    host: "Host"
    manifest: AppManifest
    game_instance: "GameInstance"
    source_url: Optional[str]
    window: Optional[AppWindow] = None
    alt1api: Optional[Alt1Api] = None
    web_profile: Optional[WebProfile] = None

    def __init__(self, host, manifest, game_instance, source_url=None):
        self.host = host
        self.manifest = manifest
        self.game_instance = game_instance
        self.source_url = source_url

        self.game_instance.on("active", self.on_game_active_change)

    def get_window(self, **kwargs) -> AppWindow:
        self.window = AppWindow(app=self, **kwargs)
        return self.window

    def get_api(self) -> Alt1Api:
        if self.alt1api:
            return self.alt1api

        self.alt1api = Alt1Api(app=self, parent=self.window)
        return self.alt1api

    def get_web_profile(self, parent=None) -> WebProfile:
        if self.web_profile:
            return self.web_profile

        if not self.window:
            # This method is called in get_window, so self.window is not set
            self.window = parent

        self.web_profile = WebProfile(app=self, parent=self.window)
        return self.web_profile

    @property
    def absolute_app_url(self) -> str:
        if self.source_url:
            return urljoin(self.source_url, self.manifest["appUrl"])

        return self.manifest["appUrl"]

    @property
    def absolute_config_url(self) -> str:
        if self.source_url:
            return urljoin(self.source_url, self.manifest["configUrl"])

        return self.manifest["configUrl"]

    @property
    def absolute_icon_url(self) -> Optional[str]:
        if self.source_url and "iconUrl" in self.manifest:
            return urljoin(self.source_url, self.manifest["iconUrl"])

        return self.manifest.get("iconUrl")

    @property
    def permissions(self) -> List[str]:
        return self.manifest["permissions"].split(",")

    def has_permission(self, name: str) -> bool:
        return name in self.permissions

    def on_game_active_change(self, active):
        if not self.window:
            return

        if active:
            self.window.setWindowState(self.window.windowState() & ~Qt.WindowMinimized)
        else:
            self.window.setWindowState(self.window.windowState() | Qt.WindowMinimized)

        self.window.show()
