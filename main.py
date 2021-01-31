import logging
import sys
import traceback

import click
from PySide2.QtWidgets import QApplication, QMessageBox

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
@click.argument("app_url")
def main(app_url, game_index, qt_args):
    logging.basicConfig(level=logging.DEBUG)

    logging.info("Starting QtWebEngine")
    browser.init()
    app = QApplication(["runekit", *qt_args])
    try:
        host = Host()

        game_manager = get_platform_manager()
        logging.info("Scanning for game instances")
        game_instances = game_manager.get_instances()
        logging.info("Found %d instances", len(game_instances))
        game = game_instances[game_index]

        logging.info("Loading app")
        host.start_app(app_url, game)

        app.exec_()
        game_manager.stop()
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


if __name__ == "__main__":
    main()
