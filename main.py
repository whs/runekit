import logging
import signal
import sys
import traceback

import click
from PySide2.QtCore import QSettings, Qt, QTimer
from PySide2.QtWidgets import (
    QApplication,
    QMessageBox,
)

import runekit._resources
from runekit import browser
from runekit.game import get_platform_manager
from runekit.host import Host


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.option("--game-index", default=0, help="Game instance index, starting from 0")
@click.argument("qt_args", nargs=-1, type=click.UNPROCESSED)
@click.argument("app_url", required=False)
def main(app_url, game_index, qt_args):
    logging.basicConfig(level=logging.DEBUG)

    logging.info("Starting QtWebEngine")
    browser.init()

    app = QApplication(["runekit", *qt_args])
    app.setQuitOnLastWindowClosed(False)
    app.setOrganizationName("cupco.de")
    app.setOrganizationDomain("cupco.de")
    app.setApplicationName("RuneKit")

    signal.signal(signal.SIGINT, lambda no, frame: app.quit())

    timer = QTimer()
    timer.start(300)
    timer.timeout.connect(lambda: None)

    QSettings.setDefaultFormat(QSettings.IniFormat)

    try:
        game_manager = get_platform_manager()
        host = Host(game_manager)

        if app_url == "settings":
            host.open_settings()
            host.setting_dialog.setAttribute(Qt.WA_DeleteOnClose)
            host.setting_dialog.destroyed.connect(app.quit)
        elif app_url:
            logging.info("Loading app")
            game_app = host.launch_app_from_url(app_url)
            game_app.window.destroyed.connect(app.quit)
        else:
            if not host.app_store.has_default_apps():
                host.app_store.load_default_apps()

        app.exec_()
        sys.exit(0)
    except Exception as e:
        msg = QMessageBox(
            QMessageBox.Critical,
            "Oh No!",
            f"Fatal error: \n\n{e.__class__.__name__}: {e}",
        )
        msg.setDetailedText(traceback.format_exc())
        msg.exec_()

        raise
    finally:
        if game_manager is not None:
            logging.debug("Stopping game manager")
            game_manager.stop()


if __name__ == "__main__":
    main()
