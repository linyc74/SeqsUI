import sys
from PyQt5.QtWidgets import QApplication
from .view import View
from .model import Model
from .controller import Controller


__VERSION__ = '1.1.0-beta'


class Main:

    APP_ID = f'NYCU.Dentistry.SeqsUI.{__VERSION__}'

    model: Model
    view: View
    controller: Controller

    def main(self):
        self.config_taskbar_icon()

        app = QApplication(sys.argv)

        self.model = Model()
        self.view = View(self.model)
        self.controller = Controller(self.model, self.view)

        sys.exit(app.exec_())

    def config_taskbar_icon(self):
        try:
            from ctypes import windll  # only exists on Windows
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.APP_ID)
        except ImportError as e:
            print(e, flush=True)
