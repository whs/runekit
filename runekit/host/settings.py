import sys
from typing import TYPE_CHECKING

from PySide2.QtCore import QSize, Qt, Slot, QTimer
from PySide2.QtWidgets import (
    QTabWidget,
    QVBoxLayout,
    QMainWindow,
    QWidget,
    QFormLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QTableWidget,
    QHBoxLayout,
    QTreeView,
    QSpinBox,
)

from .applications import ApplicationModel
from ..ui import TooltipNotifier, TrayIconNotifier

if TYPE_CHECKING:
    from .host import Host


class SettingsDialog(QMainWindow):
    def __init__(self, host: "Host", **kwargs):
        super().__init__(flags=Qt.Dialog, **kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.host = host
        self._layout()
        self.setWindowTitle("RuneKit Settings")

    def _layout(self):
        tab = QTabWidget(self)
        tab.addTab(ApplicationPage(self.host, parent=self), "Applications")
        tab.addTab(InterfacePage(self.host, parent=self), "Interface")

        self.setCentralWidget(tab)
        self.setContentsMargins(11, 11, 11, 11)

    def sizeHint(self) -> QSize:
        return QSize(500, 300)


class ApplicationPage(QWidget):
    host: "Host"

    def __init__(self, host: "Host", **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self._layout()

    def _layout(self):
        layout = QHBoxLayout(self)
        self.setLayout(layout)

        tree = QTreeView(self)
        model = ApplicationModel(self)
        tree.setModel(model)
        tree.setUniformRowHeights(True)
        layout.addWidget(tree, 1)


class InterfacePage(QWidget):
    host: "Host"

    def __init__(self, host: "Host", **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self._layout()

    def _layout(self):
        layout = QFormLayout(self)
        self.setLayout(layout)

        tooltip_label = QLabel("Display tooltips as", self)
        tooltip_field = QComboBox(self)
        tooltip_field.insertItem(0, "Disabled")
        tooltip_field.insertItem(1, "Notification")  # XXX: Check support
        tooltip_field.insertItem(2, "Cursor tooltip")
        tooltip_field.currentIndexChanged.connect(self.preview_tooltip)
        layout.addRow(tooltip_label, tooltip_field)

        border_field = QCheckBox("Styled window border", self)
        border_field.setDisabled(sys.platform == "darwin")
        border_field.setChecked(sys.platform != "darwin")
        layout.addRow(None, border_field)

        # I think this doesn't belong to "Interface"
        # either rename it to settings or make separate game tab
        refresh_label = QLabel("Refresh interval", self)
        refresh_layout = QHBoxLayout(self)
        refresh_field = QSpinBox(self)
        refresh_field.setRange(100, 2000)
        refresh_field.setSingleStep(100)
        refresh_field.setValue(100)
        refresh_layout.addWidget(refresh_field, 1)
        refresh_unit = QLabel("ms", self)
        refresh_layout.addWidget(refresh_unit, 0)
        layout.addRow(refresh_label, refresh_layout)

    @Slot(int)
    def preview_tooltip(self, index: int):
        if index == 1:
            notifier = TrayIconNotifier()
        elif index == 2:
            notifier = TooltipNotifier()
        else:
            return

        if hasattr(self, "_last_notifier"):
            self._last_notifier.notify("")

        self._last_notifier = notifier
        notifier.notify("This is an example notification")
        QTimer.singleShot(3000, lambda: notifier.notify(""))
