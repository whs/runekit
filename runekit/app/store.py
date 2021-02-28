from pathlib import Path
import json
import logging
import hashlib
from typing import Iterator, Tuple, Optional
from urllib.parse import urljoin

import requests
from PySide2.QtCore import (
    QObject,
    QSettings,
    QThread,
    Signal,
    Slot,
    QStandardPaths,
)
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtWidgets import QProgressDialog

from runekit.alt1.schema import AppManifest
from runekit.alt1.utils import fetch_bom_json

REGISTRY_URL = "https://runeapps.org/data/alt1/defaultapps.json"

logger = logging.getLogger(__name__)


def app_id(manifest_url):
    assert "://" in manifest_url
    return hashlib.blake2b(manifest_url.encode("utf8"), digest_size=16).hexdigest()


class _FetchRegistryThread(QThread):
    progress = Signal(int)
    items = Signal(int)
    label = Signal(str)

    canceled = False

    def __init__(self, parent: "AppStore"):
        super().__init__(parent=parent)
        self.appstore = parent

    def run(self):
        try:
            default_apps = fetch_bom_json(REGISTRY_URL)
            self.items.emit(len(default_apps) + 1)
            self.progress.emit(1)
            for index, app in enumerate(default_apps):
                self.label.emit(f"Installing {app['name']}")
                url = urljoin(REGISTRY_URL, app["url"])
                self.add_app(url, app["folder"])
                self.progress.emit(index + 2)

                if self.canceled:
                    return
        finally:
            self.items.emit(100)
            self.progress.emit(100)

    def add_app(self, url, folder=""):
        manifest = fetch_bom_json(url)
        try:
            self.appstore.add_app(url, manifest)
            if folder != "":
                self.appstore.add_app_to_folder(url, folder)
        except AddAppError:
            logger.warning("Unable to add application %s", url, exc_info=True)

    @Slot()
    def cancel(self):
        self.canceled = True


class AppStore(QObject):
    app_change = Signal()

    def __init__(self):
        super().__init__()
        self.settings = QSettings(self)

        qt_write_base = Path(
            QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
        )
        qt_write_base.mkdir(exist_ok=True)

        self.icon_write_dir = qt_write_base / "app_icons"
        self.icon_write_dir.mkdir(exist_ok=True)

    def has_default_apps(self) -> bool:
        return self.settings.value("apps/_meta/isDefaultLoaded")

    def load_default_apps(self):
        def on_progress(value):
            if value != self.default_app_progress.maximum():
                return

            self.settings.setValue("apps/_meta/isDefaultLoaded", True)
            logger.info("Default apps loaded")
            self.default_app_thread.progress.disconnect(on_progress)
            del self.default_app_progress
            del self.default_app_thread

        self.default_app_progress = QProgressDialog(
            "Loading default apps", "Cancel", 0, 100
        )

        self.default_app_thread = _FetchRegistryThread(self)
        self.default_app_thread.progress.connect(self.default_app_progress.setValue)
        self.default_app_thread.progress.connect(on_progress)
        self.default_app_thread.items.connect(self.default_app_progress.setMaximum)
        self.default_app_thread.label.connect(self.default_app_progress.setLabelText)
        self.default_app_progress.canceled.connect(self.default_app_thread.cancel)
        self.default_app_thread.start()

        self.default_app_progress.show()

    def add_app(self, manifest_url: str, manifest: AppManifest):
        appid = app_id(manifest_url)

        try:
            manifest["appUrl"] = urljoin(manifest_url, manifest["appUrl"])
            manifest["iconUrl"] = (
                urljoin(manifest_url, manifest["iconUrl"])
                if manifest["iconUrl"]
                else ""
            )
            manifest["configUrl"] = urljoin(manifest_url, manifest["configUrl"])
        except KeyError:
            raise AddAppError(manifest_url)

        if manifest["iconUrl"]:
            self.download_app_icon(appid, manifest["iconUrl"])

        self.settings.setValue(f"apps/{appid}", json.dumps(manifest))
        self.app_change.emit()
        logger.info(
            "Application %s (%s:%s) installed", manifest["appName"], appid, manifest_url
        )

    def add_app_to_folder(self, manifest_url: str, folder: str):
        assert "/" not in folder
        appid = app_id(manifest_url)
        settings = QSettings()
        settings.beginGroup(f"apps/_folder/{folder}")

        last_id = 0
        for key in self.settings.childKeys():
            last_id = max(int(key), last_id)
            if appid == self.settings.value(key):
                self.settings.endGroup()
                return

        keys = [int(x) for x in self.settings.childKeys()]
        last_id = max(keys) if keys else 0
        settings.endGroup()

        settings.setValue(f"apps/_folder/{folder}/{last_id + 1}", appid)
        self.app_change.emit()

    def download_app_icon(self, appid: str, url: str):
        dest = self.icon_write_dir / (appid + ".png")
        req = requests.get(url)
        with dest.open("wb") as fp:
            fp.write(req.content)

        logger.info("App icon %s wrote to %s", appid, str(dest))

    def icon(self, appid: str) -> Optional[QIcon]:
        fn = QStandardPaths.locate(
            QStandardPaths.AppConfigLocation, "app_icons/" + appid + ".png"
        )
        if fn == "":
            return None

        return QIcon(QPixmap(fn))

    def __iter__(self) -> Iterator[Tuple[str, AppManifest]]:
        settings = QSettings()
        settings.beginGroup("apps")
        for appid in settings.childKeys():
            if appid.startswith("_"):
                continue

            manifest = json.loads(settings.value(appid))
            yield appid, manifest

        settings.endGroup()

    def __getitem__(self, item: str) -> AppManifest:
        assert not item.startswith("_")
        return json.loads(self.settings.value(f"apps/{item}"))


class AddAppError(ValueError):
    def __init__(self, url):
        super().__init__(f"Unable to parse manifest of application at {url}")
