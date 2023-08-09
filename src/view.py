from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QPushButton, \
    QFileDialog, QMessageBox, QGridLayout, QDialog, QFormLayout, QLineEdit, QDialogButtonBox
from os.path import dirname
from typing import List, Tuple
from .model import Model


class Table(QTableWidget):

    model: Model

    def __init__(self, model: Model):
        super().__init__()
        self.model = model
        self.refresh_table()

    def refresh_table(self):
        df = self.model.get_dataframe()

        self.setRowCount(len(df.index))
        self.setColumnCount(len(df.columns))

        self.setHorizontalHeaderLabels(df.columns)
        for i in range(len(df.index)):
            for j in range(len(df.columns)):
                item = QTableWidgetItem(str(df.iloc[i, j]))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # makes the item immutable, i.e. user cannot edit it
                self.setItem(i, j, item)

        self.resizeColumnsToContents()

    def get_selected_rows(self) -> List[int]:
        ret = []
        for item in self.selectedItems():
            ith_row = item.row()
            if ith_row not in ret:
                ret.append(ith_row)
        return ret

    def get_selected_columns(self) -> List[str]:
        ret = []
        for item in self.selectedItems():
            ith_col = item.column()
            column = self.horizontalHeaderItem(ith_col).text()
            if column not in ret:
                ret.append(column)
        return ret


class View(QWidget):

    TITLE = 'Seqs UI'
    ICON_PNG = f'{dirname(__file__)}/logo.png'
    WIDTH, HEIGHT = 1280, 768
    BUTTON_NAME_TO_LABEL = {
        'read_sequencing_table': 'Read Sequencing Table',
        'import_new_entries': 'Import New Entries',
        'save_sequencing_table': 'Save Sequencing Table',

        'sort_ascending': 'Sort (A to Z)',
        'sort_descending': 'Sort (Z to A)',
        'delete_selected_rows': 'Delete Selected Rows',
        'reset_table': 'Reset Table',

        'copy_selected_fastq_files': 'Copy Selected Fastq Files',
        # 'build_execution_sheet': 'Build Execution Sheet',
        # 'build_cbioportal_data': 'Build cBioPortal Data',
    }
    BUTTON_NAME_TO_POSITION = {
        'read_sequencing_table': (0, 0),
        'import_new_entries': (1, 0),
        'save_sequencing_table': (2, 0),

        'sort_ascending': (0, 1),
        'sort_descending': (1, 1),
        'delete_selected_rows': (2, 1),
        'reset_table': (3, 1),

        'copy_selected_fastq_files': (0, 2),
        # 'build_execution_sheet': (1, 2),
        # 'build_cbioportal_data': (2, 2),
    }

    model: Model
    vertical_layout: QVBoxLayout
    table: Table
    button_grid: QGridLayout

    def __init__(self, model: Model):
        super().__init__()
        self.model = model

        self.setWindowTitle(self.TITLE)
        self.setWindowIcon(QIcon(self.ICON_PNG))
        self.resize(self.WIDTH, self.HEIGHT)

        self.__init__vertical_layout()
        self.__init__main_table()
        self.__init__buttons()
        self.__init__methods()

    def __init__vertical_layout(self):
        self.vertical_layout = QVBoxLayout()
        self.setLayout(self.vertical_layout)

    def __init__main_table(self):
        self.table = Table(self.model)
        self.vertical_layout.addWidget(self.table)

    def __init__buttons(self):
        self.button_grid = QGridLayout()
        self.vertical_layout.addLayout(self.button_grid)

        for name, label in self.BUTTON_NAME_TO_LABEL.items():
            setattr(self, f'button_{name}', QPushButton(label))
            button = getattr(self, f'button_{name}')
            pos = self.BUTTON_NAME_TO_POSITION[name]
            self.button_grid.addWidget(button, *pos)

    def __init__methods(self):
        self.file_dialog_open_csv = FileDialogOpenCsv(self)
        self.file_dialog_save_csv = FileDialogSaveCsv(self)
        self.file_dialog_open_directory = FileDialogOpenDirectory(self)
        self.message_box_info = MessageBoxInfo(self)
        self.message_box_error = MessageBoxError(self)
        self.message_box_yes_no = MessageBoxYesNo(self)
        self.dialog_read1_read2_suffix = DialogRead1Read2Suffix(self)

    def refresh_table(self):
        self.table.refresh_table()

    def get_selected_rows(self) -> List[int]:
        return self.table.get_selected_rows()

    def get_selected_columns(self) -> List[str]:
        return self.table.get_selected_columns()


class FileDialog:

    parent: QWidget

    def __init__(self, parent: QWidget):
        self.parent = parent


class FileDialogOpenCsv(FileDialog):

    def __call__(self) -> str:
        fpath, ftype = QFileDialog.getOpenFileName(
            parent=self.parent,
            caption='Open',
            filter='All Files (*.*);;CSV files (*.csv)',
            initialFilter='CSV files (*.csv)',
            options=QFileDialog.DontUseNativeDialog
        )
        return fpath


class FileDialogSaveCsv(FileDialog):

    def __call__(self) -> str:
        fpath, ftype = QFileDialog.getSaveFileName(
            parent=self.parent,
            caption='Save As',
            filter='All Files (*.*);;CSV files (*.csv)',
            initialFilter='CSV files (*.csv)',
            options=QFileDialog.DontUseNativeDialog
        )
        return fpath


class FileDialogOpenDirectory(FileDialog):

    def __call__(self, caption: str) -> str:
        fpath = QFileDialog.getExistingDirectory(
            parent=self.parent,
            caption=caption,
            options=QFileDialog.DontUseNativeDialog
        )
        return fpath


class MessageBox:

    TITLE: str
    ICON: QMessageBox.Icon

    box: QMessageBox

    def __init__(self, parent: QWidget):
        self.box = QMessageBox(parent)
        self.box.setWindowTitle(self.TITLE)
        self.box.setIcon(self.ICON)

    def __call__(self, msg: str):
        self.box.setText(msg)
        self.box.exec_()


class MessageBoxInfo(MessageBox):

    TITLE = 'Info'
    ICON = QMessageBox.Information


class MessageBoxError(MessageBox):

    TITLE = 'Error'
    ICON = QMessageBox.Warning


class MessageBoxYesNo(MessageBox):

    TITLE = ' '
    ICON = QMessageBox.Question

    def __init__(self, parent: QWidget):
        super(MessageBoxYesNo, self).__init__(parent)
        self.box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self.box.setDefaultButton(QMessageBox.No)

    def __call__(self, msg: str) -> bool:
        self.box.setText(msg)
        return self.box.exec_() == QMessageBox.Yes


class DialogRead1Read2Suffix:

    dialog: QDialog
    layout: QFormLayout
    line_edit1: QLineEdit
    line_edit2: QLineEdit
    button_box: QDialogButtonBox

    def __init__(self, parent: QWidget):
        self.__init__dialog(parent=parent)
        self.__init__layout()
        self.__init__line_edits()
        self.__init__button_box()

    def __init__dialog(self, parent: QWidget):
        self.dialog = QDialog(parent=parent)
        self.dialog.setWindowTitle(' ')

    def __init__layout(self):
        self.layout = QFormLayout(parent=self.dialog)

    def __init__line_edits(self):
        self.line_edit1 = QLineEdit('_R1.fastq.gz', parent=self.dialog)
        self.line_edit2 = QLineEdit('_R2.fastq.gz', parent=self.dialog)
        self.layout.addRow('Read 1 Suffix:', self.line_edit1)
        self.layout.addRow('Read 2 Suffix:', self.line_edit2)

    def __init__button_box(self):
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self.dialog)
        self.button_box.accepted.connect(self.dialog.accept)
        self.button_box.rejected.connect(self.dialog.reject)
        self.layout.addWidget(self.button_box)

    def __call__(self) -> Tuple[str, str]:
        result = self.dialog.exec_()
        if result == QDialog.Accepted:
            return self.line_edit1.text(), self.line_edit2.text()
        else:
            return '', ''
