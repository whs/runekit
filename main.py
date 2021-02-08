import logging
import sys
import traceback

import click
from PySide2.QtWidgets import (
    QApplication,
    QMessageBox,
    QInputDialog,
    QDialog,
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
    game_manager = None
    try:
        host = Host()

        if app_url == "settings":
            settings_wnd = host.open_settings()
            settings_wnd.destroyed.connect(app.quit)
        else:
            game_manager = get_platform_manager()
            logging.info("Scanning for game instances")
            game_instances = game_manager.get_instances()
            logging.info("Found %d instances", len(game_instances))
            if len(game_instances) == 0:
                QMessageBox(
                    QMessageBox.Critical,
                    "Game not found",
                    "Cannot find RuneScape. Launch the game first",
                ).exec_()
                return

            game = game_instances[game_index]

            if app_url is None:
                dialog = QInputDialog()
                dialog.setComboBoxEditable(True)
                dialog.setComboBoxItems(
                    [
                        "https://runeapps.org/apps/alt1/example/appconfig.json",
                        "https://runeapps.org/apps/clue/appconfig.json",
                        "https://runeapps.org/apps/alt1/afkscape/appconfig.json",
                    ]
                )
                dialog.setLabelText("Enter appconfig URL")
                dialog.setWindowTitle("RuneKit")
                if dialog.exec_() == QDialog.DialogCode.Rejected:
                    return
                app_url = dialog.textValue()

            logging.info("Loading app")
            game_app = host.start_app(app_url, game)
            game_app.window.destroyed.connect(app.quit)

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
            game_manager.stop()


if __name__ == "__main__":
    main()
