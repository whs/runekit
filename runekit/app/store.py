import sys
import traceback
from pathlib import Path
import json
import logging
import hashlib
from typing import Iterator, Tuple, Optional, Union, List
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
from PySide2.QtWidgets import QProgressDialog, QMessageBox

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
    failed = Signal(tuple)

    canceled = False

    def __init__(
        self,
        parent: "AppStore",
        apps_manifest: Optional[str] = None,
        apps: Optional[List[str]] = None,
    ):
        super().__init__(parent=parent)
        assert (not apps_manifest and apps) or (
            not apps and apps_manifest
        ), "One of apps_manifest or apps must be set but not both. apps_manifest={}, apps={}".format(
            apps_manifest, apps
        )

        self.appstore = parent
        self.apps_manifest = apps_manifest
        self.apps = apps

    def run(self):
        try:
            progress_extra = 0
            if self.apps_manifest:
                apps = fetch_bom_json(REGISTRY_URL)
                self.items.emit(len(apps) + 1)
                self.progress.emit(1)
                progress_extra = 1
            else:
                apps = self.apps
                self.items.emit(len(apps))

            for index, app in enumerate(apps):
                if type(app) == str:
                    self.label.emit(f"Installing app {app}")
                    self.add_app(app)
                else:
                    self.label.emit(f"Installing {app['name']}")
                    url = urljoin(REGISTRY_URL, app["url"])
                    self.add_app(url, app["folder"])

                self.progress.emit(index + progress_extra + 1)

                if self.canceled:
                    return
        finally:
            self.items.emit(100)
            self.progress.emit(100)

    def add_app(self, url, folder=""):
        try:
            manifest = fetch_bom_json(url)
            self.appstore.add_app(url, manifest)
            self.appstore.add_app_to_folder(app_id(url), folder)
        except:
            logger.warning("Unable to add application %s", url, exc_info=True)
            self.failed.emit(sys.exc_info())

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
        qt_write_base.mkdir(parents=True, exist_ok=True)

        self.icon_write_dir = qt_write_base / "app_icons"
        self.icon_write_dir.mkdir(exist_ok=True)

    def has_default_apps(self) -> bool:
        return self.settings.value("apps/_meta/isDefaultLoaded")

    def load_default_apps(self):
        def on_progress(value):
            if value != self.app_progress.maximum():
                return

            self.settings.setValue("apps/_meta/isDefaultLoaded", True)
            logger.info("Default apps loaded")
            self.add_app_thread.progress.disconnect(on_progress)
            del self.app_progress
            del self.add_app_thread

        self.app_progress = QProgressDialog("Loading default apps", "Cancel", 0, 100)

        self.add_app_thread = _FetchRegistryThread(self, apps_manifest=REGISTRY_URL)
        self.add_app_thread.progress.connect(self.app_progress.setValue)
        self.add_app_thread.progress.connect(on_progress)
        self.add_app_thread.items.connect(self.app_progress.setMaximum)
        self.add_app_thread.label.connect(self.app_progress.setLabelText)
        self.app_progress.canceled.connect(self.add_app_thread.cancel)
        self.add_app_thread.start()

        self.app_progress.show()

    def add_app_ui(self, manifests: List[str]):
        def on_progress(value):
            if value != self.app_progress.maximum():
                return

            self.add_app_thread.progress.disconnect(on_progress)
            del self.app_progress
            del self.add_app_thread

        def on_failed(exc_info):
            msg = QMessageBox(
                QMessageBox.Critical,
                "Fail to add application",
                f"Failed to add application: \n\n{exc_info[0].__name__}: {exc_info[1]}",
            )
            msg.setDetailedText("".join(traceback.format_exception(*exc_info)))
            msg.exec_()

        self.app_progress = QProgressDialog("Installing app", "Cancel", 0, 100)

        self.add_app_thread = _FetchRegistryThread(self, apps=manifests)
        self.add_app_thread.progress.connect(self.app_progress.setValue)
        self.add_app_thread.progress.connect(on_progress)
        self.add_app_thread.items.connect(self.app_progress.setMaximum)
        self.add_app_thread.label.connect(self.app_progress.setLabelText)
        self.add_app_thread.failed.connect(on_failed)
        self.app_progress.canceled.connect(self.add_app_thread.cancel)
        self.add_app_thread.start()

        self.app_progress.exec_()

    def add_app(self, manifest_url: str, manifest: AppManifest):
        appid = app_id(manifest_url)

        try:
            manifest["appUrl"] = urljoin(manifest_url, manifest["appUrl"])
            manifest["iconUrl"] = (
                urljoin(manifest_url, manifest["iconUrl"])
                if "iconUrl" in manifest and manifest["iconUrl"]
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

    def mkdir(self, folder: str):
        assert folder
        assert "/" not in folder

        settings = QSettings()
        settings.beginGroup(f"apps/_folder/{folder}")
        settings.setValue("_dir", "true")
        self.app_change.emit()

    def add_app_to_folder(self, appid: str, folder: str = "", _emit=True):
        assert "/" not in folder
        settings = QSettings()
        settings.beginGroup(f"apps/_folder/{folder}")

        last_id = 0
        for key in settings.childKeys():
            if "_" in key:
                continue

            last_id = max(int(key), last_id)
            if appid == settings.value(key):
                settings.endGroup()
                return

        keys = [int(x) for x in settings.childKeys() if "_" not in x]
        last_id = max(keys) if keys else 0
        settings.endGroup()

        settings.setValue(f"apps/_folder/{folder}/{last_id + 1}", appid)

        if _emit:
            self.app_change.emit()

    def delete_app_from_folder(self, appid: str, folder: str):
        assert "/" not in folder
        settings = QSettings()
        settings.beginGroup(f"apps/_folder/{folder}")

        for key in settings.childKeys():
            if appid == settings.value(key):
                settings.remove(key)
                self.app_change.emit()
                return

    def remove_app(self, appid: str):
        settings = QSettings()
        settings.beginGroup("apps/_folder/")

        def recurse():
            for key in settings.childKeys():
                if settings.value(key) == appid:
                    settings.remove(key)

            for childGroup in settings.childGroups():
                settings.beginGroup(childGroup)
                recurse()
                settings.endGroup()

        recurse()

        self.settings.remove(f"apps/{appid}")

        icon_file = self.icon_write_dir / (appid + ".png")
        icon_file.unlink(True)

        self.app_change.emit()

    def rmdir(self, folder: str):
        assert folder
        assert "/" not in folder

        settings = QSettings()
        settings.beginGroup(f"apps/_folder/{folder}")

        for key in settings.childKeys():
            if "_" in key:
                continue

            try:
                int(key)
            except ValueError:
                continue

            self.add_app_to_folder(settings.value(key), "", _emit=False)

        settings.remove("")
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

    def all_apps(self) -> Iterator[Tuple[str, AppManifest]]:
        settings = QSettings()
        settings.beginGroup("apps")
        for appid in settings.childKeys():
            if appid.startswith("_"):
                continue

            manifest = json.loads(settings.value(appid))
            yield appid, manifest

        settings.endGroup()

    def list_app(self, root: str) -> Iterator[Tuple[str, Union[AppManifest, None]]]:
        settings = QSettings()

        settings.beginGroup(f"apps/_folder/" + root)
        for key in settings.childGroups():
            yield key, None
        for key in settings.childKeys():
            try:
                int(key)
            except ValueError:
                continue

            appid = settings.value(key)
            yield appid, self[appid]

    def __iter__(self):
        yield from self.all_apps()

    def __getitem__(self, item: str) -> AppManifest:
        assert not item.startswith("_")
        return json.loads(self.settings.value(f"apps/{item}"))


class AddAppError(ValueError):
    def __init__(self, url):
        super().__init__(f"Unable to parse manifest of application at {url}")
