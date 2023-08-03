from os.path import dirname
from PyQt5 import QtGui
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QMessageBox
from .model import Model


class View(QWidget):

    BUTTON_NAME_TO_LABEL = {
        'read_sequencing_table': 'Read Sequencing Table',
        'import_new_entries': 'Import New Entries',
        'save_sequencing_table': 'Save Sequencing Table',
        'reset': 'Reset',
    }

    model: Model
    layout: QVBoxLayout
    table: QTableWidget

    def __init__(self, model: Model):
        super().__init__()
        self.model = model

        self.resize(1280, 768)
        self.setWindowIcon(QtGui.QIcon(f'{dirname(__file__)}/logo.png'))
        self.setWindowTitle('Seqs UI')

        self.init_layout()
        self.init_table()
        self.init_buttons()

    def init_layout(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def init_table(self):
        self.table = QTableWidget()
        self.refresh_table()
        self.layout.addWidget(self.table)

    def init_buttons(self):
        for name, label in self.BUTTON_NAME_TO_LABEL.items():
            setattr(self, f'button_{name}', QPushButton(label))
            self.layout.addWidget(getattr(self, f'button_{name}'))

    def refresh_table(self):
        df = self.model.get_dataframe()

        self.table.setRowCount(len(df.index))
        self.table.setColumnCount(len(df.columns))

        self.table.setHorizontalHeaderLabels(df.columns)
        for i in range(len(df.index)):
            for j in range(len(df.columns)):
                s = str(df.iloc[i, j])
                self.table.setItem(i, j, QTableWidgetItem(s))

        self.table.resizeColumnsToContents()

    def open_csv_file_dialog(self) -> str:
        fpath, ftype = QFileDialog.getOpenFileName(
            parent=self,
            caption='Open',
            filter='All Files (*.*);;CSV files (*.csv)',
            initialFilter='CSV files (*.csv)',
            options=QFileDialog.DontUseNativeDialog
        )
        return fpath

    def save_csv_file_dialog(self) -> str:
        fpath, ftype = QFileDialog.getSaveFileName(
            parent=self,
            caption='Save As',
            filter='All Files (*.*);;CSV files (*.csv)',
            initialFilter='CSV files (*.csv)',
            options=QFileDialog.DontUseNativeDialog
        )
        return fpath

    def show_error(self, msg: str):
        box = QMessageBox(self)
        box.setWindowTitle('Error')
        box.setIcon(QMessageBox.Warning)
        box.setText(msg)
        box.show()
