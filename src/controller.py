from .view import View
from .model import Model


class Controller:

    model: Model
    view: View

    def __init__(self, model: Model, view: View):
        self.model = model
        self.view = view
        self.connect_button_actions()
        self.view.show()

    def connect_button_actions(self):
        for name in self.view.BUTTON_NAME_TO_LABEL.keys():
            button = getattr(self.view, f'button_{name}')
            method = getattr(self, f'action_{name}', None)
            if method is not None:
                button.clicked.connect(method)
            else:
                print(f'WARNING: method "action_{name}" does not exist in the Controller')

    def action_read_sequencing_table(self):
        csv = self.view.open_csv_file_dialog()
        if csv == '':
            return

        success, msg = self.model.read_sequencing_table(csv=csv)
        if not success:
            self.view.show_error(msg=msg)

        self.view.refresh_table()

    def action_import_new_entries(self):
        csv = self.view.open_csv_file_dialog()
        if csv == '':
            return

        success, msg = self.model.import_new_entries(csv=csv)
        if not success:
            self.view.show_error(msg=msg)

        self.view.refresh_table()

    def action_save_sequencing_table(self):
        csv = self.view.save_csv_file_dialog()
        if csv == '':
            return
        self.model.save_sequencing_table(csv=csv)

    def action_reset(self):
        self.model.reset_dataframe()
        self.view.refresh_table()
