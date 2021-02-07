from PySide2.QtCore import QAbstractItemModel, Qt, QModelIndex


class ApplicationModel(QAbstractItemModel):
    h_columns = ("Name", "URL", "Description")

    def columnCount(self, parent: QModelIndex) -> int:
        return len(self.h_columns)

    def rowCount(self, parent: QModelIndex) -> int:
        if parent.isValid():
            return 0

        return 1

    def data(self, index: QModelIndex, role: int):
        if role != Qt.DisplayRole:
            return None

        col = index.column()
        if col == 0:
            return "TestApp"
        elif col == 1:
            return "https://runeapps.org/apps/alt1/example/appconfig.json"
        elif col == 2:
            return "Lorem ipsum dolor sit amet"

    def index(self, row: int, column: int, parent: QModelIndex) -> QModelIndex:
        return self.createIndex(row, column)

    def parent(self, index: QModelIndex) -> QModelIndex:
        return QModelIndex()

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role != Qt.DisplayRole:
            return None
        if orientation != Qt.Orientation.Horizontal:
            return None

        return self.h_columns[section]
