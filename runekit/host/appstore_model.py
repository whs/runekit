import typing
import json
from typing import Optional, TypedDict, Union, List

from PySide2.QtCore import QAbstractItemModel, Qt, QModelIndex, QMimeData
from PySide2.QtGui import QIcon

from runekit.alt1.schema import AppManifest
from runekit.app import AppStore

MIMETYPE = "application/x-qabstractitemmodeldatalist"


class _InternalData(TypedDict):
    id: str
    data: Optional[AppManifest]
    index: QModelIndex
    parent: Union[QModelIndex, None]
    children: List["_InternalData"]


class AppStoreModel(QAbstractItemModel):
    h_columns = ("Name", "URL", "Description")
    model: List[_InternalData]

    def __init__(self, parent, store: AppStore):
        super().__init__(parent)
        self.store = store
        self.store.app_change.connect(self.on_app_change)
        self.model = self.build_model()

    def on_app_change(self):
        self.beginResetModel()
        self.model = self.build_model()
        self.endResetModel()

    def build_model(self, root="", parent=None) -> List[_InternalData]:
        apps = self.store.list_app(root)
        out = []

        for app_id, meta in apps:
            if not meta:

                data = {
                    "id": app_id,
                    "parent": parent,
                }
                index = data["index"] = self.createIndex(len(out), 0, data)
                data["children"] = self.build_model(app_id, index)
                out.append(data)
                continue

            data = {
                "id": app_id,
                "data": meta,
                "parent": parent,
            }
            data["index"] = self.createIndex(len(out), 0, data)
            out.append(data)

        return out

    def columnCount(self, parent: QModelIndex) -> int:
        return len(self.h_columns)

    def rowCount(self, parent: QModelIndex) -> int:
        if parent.isValid():
            data = typing.cast(_InternalData, parent.internalPointer())
            return len(data["children"])

        return len(self.model)

    def data(self, index: QModelIndex, role: int):
        left_col = index.siblingAtColumn(0)
        col = index.column()
        app = typing.cast(_InternalData, left_col.internalPointer())

        if "data" not in app:
            # Folder
            if role == Qt.DisplayRole:
                if col == 0:
                    return app["id"]
            elif role == Qt.DecorationRole:
                if col == 0:
                    return QIcon.fromTheme("folder")

            return None

        if role in (Qt.DisplayRole, Qt.ToolTipRole):
            if col == 0:
                return app["data"]["appName"]
            elif col == 1:
                return app["data"]["appUrl"]
            elif col == 2:
                return app["data"]["description"]
        elif role == Qt.DecorationRole and col == 0:
            return self.store.icon(app["id"])
        else:
            return None

    def hasChildren(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return True
        if index.column() != 0 or not index.internalPointer():
            return False

        data = typing.cast(_InternalData, index.internalPointer())
        return "data" not in data

    def index(self, row: int, column: int, parent: QModelIndex) -> QModelIndex:
        if column != 0:
            leftmost = self.index(row, 0, parent)
            return self.createIndex(row, column, leftmost.internalPointer())

        if parent.isValid():
            data = typing.cast(_InternalData, parent.internalPointer())
            return data["children"][row]["index"]

        if row >= len(self.model):
            return QModelIndex()

        return self.model[row]["index"]

    def parent(self, index: QModelIndex) -> QModelIndex:
        data = typing.cast(_InternalData, index.internalPointer())
        return data["parent"] or QModelIndex()

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        out = Qt.ItemIsSelectable | Qt.ItemIsEnabled

        if not index.isValid():
            return out | Qt.ItemIsDropEnabled

        data = typing.cast(_InternalData, index.internalPointer())
        if "data" in data:
            out |= Qt.ItemIsDragEnabled
        else:
            # Can't drag folder but can drop
            out |= Qt.ItemIsDropEnabled
        if "children" not in data:
            out |= Qt.ItemNeverHasChildren

        return out

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role != Qt.DisplayRole:
            return None
        if orientation != Qt.Orientation.Horizontal:
            return None

        return self.h_columns[section]

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.MoveAction

    def mimeData(self, indexes: List[QModelIndex]) -> QMimeData:
        indexes = [item for item in indexes if item.column() == 0]
        if not indexes:
            return None

        data = typing.cast(_InternalData, indexes[0].internalPointer())
        out = QMimeData()
        out_data = {
            "id": data["id"],
            "parent": "",
            "type": "dir" if "data" not in data else "app",
        }
        if data["parent"]:
            out_data["parent"] = data["parent"].internalPointer()["id"]

        out.setData(MIMETYPE, json.dumps(out_data).encode("ascii"))
        return out

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ) -> bool:
        data = json.loads(data.data(MIMETYPE).data())
        if parent.isValid():
            new_folder = parent.internalPointer()["id"]
        else:
            new_folder = ""

        if data["parent"] == new_folder:
            return False

        self.store.add_app_to_folder(data["id"], new_folder)
        self.store.delete_app_from_folder(data["id"], data["parent"])

        return True
