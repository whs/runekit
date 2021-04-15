from typing import Optional, TYPE_CHECKING, List
from urllib.parse import urljoin

from runekit.alt1.schema import AppManifest
from runekit.app.view.window import AppWindow
from runekit.browser import Alt1Api, WebProfile

if TYPE_CHECKING:
    from runekit.game import GameInstance
    from runekit.host import Host


class App:
    host: "Host"
    manifest: AppManifest
    app_id: str
    game_instance: "GameInstance"
    source_url: Optional[str]
    window: Optional[AppWindow] = None
    alt1api: Optional[Alt1Api] = None
    web_profile: Optional[WebProfile] = None

    def __init__(self, host, app_id, manifest, game_instance, source_url=None):
        self.host = host
        self.app_id = app_id
        self.manifest = manifest
        self.game_instance = game_instance
        self.source_url = source_url

    def close(self):
        if self.window:
            self.window.deleteLater()
            self.window = None
        if self.alt1api:
            self.alt1api.deleteLater()
            self.alt1api = None
        if self.web_profile:
            self.web_profile.deleteLater()
            self.web_profile = None

    def __del__(self):
        self.close()

    def get_window(self, **kwargs) -> AppWindow:
        self.window = AppWindow(app=self, **kwargs)
        self.window.winId()  # force native window
        # self.game_instance.embed_window(self.window.windowHandle()) # FIXME
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
        # TODO: Remove
        if self.source_url:
            return urljoin(self.source_url, self.manifest["appUrl"])

        return self.manifest["appUrl"]

    @property
    def absolute_config_url(self) -> str:
        # TODO: Remove
        if self.source_url:
            return urljoin(self.source_url, self.manifest["configUrl"])

        return self.manifest["configUrl"]

    @property
    def absolute_icon_url(self) -> Optional[str]:
        # TODO: Remove
        if self.source_url and "iconUrl" in self.manifest:
            return urljoin(self.source_url, self.manifest["iconUrl"])

        return self.manifest.get("iconUrl")

    @property
    def permissions(self) -> List[str]:
        return self.manifest["permissions"].split(",")

    def has_permission(self, name: str) -> bool:
        return name in self.permissions
