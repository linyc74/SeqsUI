import sys
from PyQt5.QtWidgets import QApplication
from .view import View
from .model import Model
from .controller import Controller


__VERSION__ = '1.1.0-beta'


class Main:

    model: Model
    view: View
    controller: Controller

    def main(self):
        app = QApplication(sys.argv)

        self.model = Model()
        self.view = View(self.model)
        self.controller = Controller(self.model, self.view)

        sys.exit(app.exec_())
