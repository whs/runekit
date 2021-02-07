import secrets
from pathlib import Path
from typing import TYPE_CHECKING

from PySide2.QtCore import QFile, QIODevice
from PySide2.QtWebEngineWidgets import QWebEngineProfile, QWebEngineScript

from runekit.browser.api import RuneKitSchemeHandler
from runekit.browser.scheme import RuneKitScheme
from runekit.utils import BASE

if TYPE_CHECKING:
    from runekit.app import App

script_file = BASE / "browser" / "alt1.js"

with script_file.open() as fp:
    src = fp.read()

_added_qwebchannel = False


class WebProfile(QWebEngineProfile):
    rpc_secret: str
    app: "App"

    def __init__(self, app=None, parent=None):
        # TODO: Persist
        super().__init__("app", parent=parent)
        self.app = app
        self.rpc_secret = secrets.token_urlsafe(64)
        self._insert_scheme_handlers()
        self._insert_alt1_api()

    def _insert_scheme_handlers(self):
        self.installUrlSchemeHandler(
            RuneKitScheme.scheme,
            RuneKitSchemeHandler(
                rpc_secret=self.rpc_secret.encode("ascii"),
                api=self.app.get_api(),
                parent=self,
            ),
        )

    def _insert_alt1_api(self):
        global _added_qwebchannel, src

        if not _added_qwebchannel:
            qwc_file = QFile(":/qtwebchannel/qwebchannel.js", parent=self)
            if not qwc_file.open(QIODevice.ReadOnly):
                raise IOError
            qwc_src = bytes(qwc_file.readAll()).decode("utf8")
            qwc_file.close()

            src = qwc_src + "\n;;\n" + src

            _added_qwebchannel = True

        script = QWebEngineScript()
        script.setName("alt1.js")
        script.setWorldId(QWebEngineScript.MainWorld)
        script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        script.setSourceCode(src.replace("%%RPC_TOKEN%%", self.rpc_secret))
        script.setRunsOnSubFrames(True)

        self.scripts().insert(script)
