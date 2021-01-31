from PySide2.QtWebEngine import QtWebEngine

from .api import Alt1WebChannel, Alt1Api
from .profile import WebProfile
from .scheme import register as register_scheme


def init():
    QtWebEngine.initialize()
    register_scheme()
