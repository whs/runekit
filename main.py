import logging
import sys

from PySide2.QtWidgets import QApplication
from PySide2.QtWebEngine import QtWebEngine

from runekit.browser import init

from runekit.game import get_platform_manager
from runekit.host import Host

AfkScape = "https://runeapps.org/apps/alt1/afkscape/appconfig.json"
ExampleApp = "https://runeapps.org/apps/alt1/example/appconfig.json"
ClueSolver = "https://runeapps.org/apps/clue/appconfig.json"


def main():
    logging.basicConfig(level=logging.DEBUG)

    logging.debug("Starting QtWebEngine")
    QtWebEngine.initialize()
    init()
    app = QApplication(sys.argv)
    host = Host()

    game_manager = get_platform_manager()
    game = game_manager.get_instances()[0]

    logging.debug("Loading app")
    host.start_app(AfkScape, game)

    app.exec_()


if __name__ == "__main__":
    main()
