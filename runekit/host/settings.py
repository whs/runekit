import json
import sys
from typing import TYPE_CHECKING

from PySide2.QtCore import QSize, Qt, Slot, QTimer, QSettings
from PySide2.QtGui import QIcon
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
    QPushButton,
    QAbstractItemView,
    QInputDialog,
    QMessageBox,
)

from .appstore_model import AppStoreModel
from ..ui import TooltipNotifier, TrayIconNotifier, AutoNotifier

if TYPE_CHECKING:
    from .host import Host


class SettingsDialog(QMainWindow):
    def __init__(self, host: "Host", **kwargs):
        super().__init__(flags=Qt.Dialog, **kwargs)
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
        return QSize(800, 500)


class ApplicationPage(QWidget):
    host: "Host"

    def __init__(self, host: "Host", **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self.model = AppStoreModel(self, self.host.app_store)
        self._layout()

    def _layout(self):
        layout = QHBoxLayout(self)
        self.setLayout(layout)

        self.tree = QTreeView(self)
        self.tree.setModel(self.model)
        self.tree.setUniformRowHeights(True)
        self.tree.setColumnWidth(0, 200)
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree.viewport().setAcceptDrops(True)
        layout.addWidget(self.tree, 1)

        buttons = QVBoxLayout()
        buttons.setAlignment(Qt.AlignTop)

        add_button = QPushButton(QIcon.fromTheme("list-add"), "", self)
        add_button.setToolTip("Add application")
        add_button.clicked.connect(self.on_add)
        buttons.addWidget(add_button)

        mkdir_button = QPushButton(QIcon.fromTheme("folder-new"), "", self)
        mkdir_button.setToolTip("Make directory")
        mkdir_button.clicked.connect(self.on_mkdir)
        buttons.addWidget(mkdir_button)

        delete_button = QPushButton(QIcon.fromTheme("list-remove"), "", self)
        delete_button.setToolTip("Remove selected item")
        delete_button.clicked.connect(self.on_delete)
        buttons.addWidget(delete_button)

        layout.addLayout(buttons)

    def on_add(self):
        dialog = QInputDialog(self)
        dialog.setLabelText("Enter appconfig.json URL")

        if dialog.exec_() == QInputDialog.Rejected:
            return

        app_url = dialog.textValue().strip()
        self.host.app_store.add_app_ui([app_url])

    def on_mkdir(self):
        dialog = QInputDialog(self)
        dialog.setLabelText("Directory name")

        if dialog.exec_() == QInputDialog.Rejected:
            return

        dirname = dialog.textValue().strip()

        if not dirname or "/" in dirname:
            QMessageBox.critical(
                self, "Invalid input", "This directory name cannot be used"
            )
            return

        self.host.app_store.mkdir(dirname)

    def on_delete(self):
        data = self.model.mimeData(self.tree.selectedIndexes())
        if not data:
            return

        data = json.loads(data.data("application/x-qabstractitemmodeldatalist").data())
        if data["type"] == "dir":
            confirm = QMessageBox.question(
                self,
                "Remove folder",
                f"Remove {data['id']}?\n\nAll applications will be moved to the top level",
            )
            if confirm == QMessageBox.StandardButton.No:
                return

            self.host.app_store.rmdir(data["id"])
        else:
            app = self.host.app_store[data["id"]]
            confirm = QMessageBox.question(
                self,
                "Remove application",
                f"Remove {app['appName']}?",
            )
            if confirm == QMessageBox.StandardButton.No:
                return

            self.host.app_store.remove_app(data["id"])
            # FIXME: Clear settings???


class InterfacePage(QWidget):
    host: "Host"

    def __init__(self, host: "Host", **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self.settings = QSettings(self)
        self._layout()

    def _layout(self):
        layout = QFormLayout(self)
        self.setLayout(layout)

        layout.addRow(
            None,
            QLabel("RuneKit needs to be restarted for changes to take effect", self),
        )

        tooltip_label = QLabel("Display tooltips as", self)
        tooltip_field = QComboBox(self)

        selected = int(
            self.settings.value("settings/tooltip", AutoNotifier.METHOD_NOTIFICATION)
        )
        selected_idx = 0
        for idx, method in enumerate(AutoNotifier.availableMethods().items()):
            tooltip_field.insertItem(idx, method[1])
            if method[0] == selected:
                selected_idx = idx

        tooltip_field.setCurrentIndex(selected_idx)

        tooltip_field.currentIndexChanged.connect(self.preview_tooltip)
        tooltip_field.currentIndexChanged.connect(self.on_tooltip_change)
        layout.addRow(tooltip_label, tooltip_field)

        border_field = QCheckBox("Styled window border", self)
        border_field.setDisabled(sys.platform == "darwin")
        border_field.setChecked(
            (self.settings.value("settings/styledBorder", "true") == "true")
            and sys.platform != "darwin"
        )
        border_field.stateChanged.connect(self.on_change_styled_border)
        layout.addRow(None, border_field)

    @Slot(int)
    def preview_tooltip(self, index: int):
        type_ = list(AutoNotifier.availableMethods().items())[index][0]
        if type_ == AutoNotifier.METHOD_NOTIFICATION:
            notifier = TrayIconNotifier()
        elif type_ == AutoNotifier.METHOD_TOOLTIP:
            notifier = TooltipNotifier()
        else:
            return

        if hasattr(self, "_last_notifier"):
            self._last_notifier.notify("")

        self._last_notifier = notifier
        notifier.notify("This is an example notification")
        QTimer.singleShot(3000, lambda: notifier.notify(""))

    @Slot(int)
    def on_tooltip_change(self, index: int):
        idx = list(AutoNotifier.availableMethods().items())[index]
        self.settings.setValue("settings/tooltip", idx[0])

    @Slot(int)
    def on_change_styled_border(self, state: int):
        checked = state == Qt.Checked
        self.settings.setValue("settings/styledBorder", checked)
