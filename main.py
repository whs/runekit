import os
import logging
import sys

import click
from PySide2.QtWidgets import QApplication
from PySide2.QtWebEngine import QtWebEngine

from runekit.browser import init

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

    logging.debug("Starting QtWebEngine")
    QtWebEngine.initialize()
    init()
    app = QApplication([sys.argv[0], *qt_args])
    host = Host()

    game_manager = get_platform_manager()
    game = game_manager.get_instances()[game_index]

    logging.debug("Loading app")
    host.start_app(app_url, game)

    app.exec_()
    sys.exit(0)


if __name__ == "__main__":
    main()
