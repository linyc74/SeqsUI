import sys
from PyQt5.QtWidgets import QApplication
from .view import View
from .model import Model
from .controller import Controller


VERSION = 'v1.2.1-beta'
STARTING_MESSAGE = f'''\
SeqsUI {VERSION}
College of Dentistry, National Yang Ming Chiao Tung University (NYCU), Taiwan
Yu-Cheng Lin, DDS, MS, PhD (ylin@nycu.edu.tw)
'''


class Main:

    APP_ID = f'NYCU.Dentistry.SeqsUI.{VERSION}'

    model: Model
    view: View
    controller: Controller

    def main(self):
        self.config_taskbar_icon()

        app = QApplication(sys.argv)

        self.model = Model()
        self.view = View(self.model)
        self.controller = Controller(self.model, self.view)

        print(STARTING_MESSAGE, flush=True)

        sys.exit(app.exec_())

    def config_taskbar_icon(self):
        try:
            from ctypes import windll  # only exists on Windows
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.APP_ID)
        except ImportError as e:
            print(e, flush=True)
