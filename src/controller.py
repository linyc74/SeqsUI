import shutil
import hashlib
from typing import List
from os.path import exists, basename
from .view import View
from .model import Model
from .tools import get_files


class Controller:

    model: Model
    view: View

    def __init__(self, model: Model, view: View):
        self.model = model
        self.view = view
        self.__init_actions()
        self.__connect_button_actions()
        self.view.show()

    def __init_actions(self):
        self.action_read_sequencing_table = ActionReadSequencingTable(self)
        self.action_import_patient_sample_sheet = ActionImportPatientSampleSheet(self)
        self.action_save_sequencing_table = ActionSaveSequencingTable(self)
        self.action_sort_ascending = ActionSortAscending(self)
        self.action_sort_descending = ActionSortDescending(self)
        self.action_delete_selected_rows = ActionDeleteSelectedRows(self)
        self.action_reset_table = ActionResetTable(self)
        self.action_copy_selected_fastq_files = ActionCopySelectedFastqFiles(self)
        self.action_build_run_table = ActionBuildRunTable(self)
        self.action_fill_in_cell_values = ActionFillInCellValues(self)
        self.action_undo = ActionUndo(self)
        self.action_redo = ActionRedo(self)

    def __connect_button_actions(self):
        for name in self.view.BUTTON_NAME_TO_LABEL.keys():
            button = getattr(self.view, f'button_{name}')
            method = getattr(self, f'action_{name}', None)
            if method is not None:
                button.clicked.connect(method)
            else:
                print(f'WARNING: method "action_{name}" does not exist in the Controller')


class Action:

    model: Model
    view: View

    def __init__(self, controller: Controller):
        self.model = controller.model
        self.view = controller.view


class ActionReadSequencingTable(Action):

    def __call__(self):
        file = self.view.file_dialog_open_table()
        if file == '':
            return

        try:
            self.model.read_sequencing_table(file=file)
            self.view.refresh_table()
        except Exception as e:
            self.view.message_box_error(msg=repr(e))


class ActionImportPatientSampleSheet(Action):

    def __call__(self):
        file = self.view.file_dialog_open_table()
        if file == '':
            return

        try:
            self.model.import_patient_sample_sheet(file=file)
            self.view.refresh_table()
        except Exception as e:
            self.view.message_box_error(msg=repr(e))


class ActionSaveSequencingTable(Action):

    def __call__(self):
        file = self.view.file_dialog_save_table(filename='sequencing_table.csv')
        if file == '':
            return
        self.model.save_sequencing_table(file=file)


class ActionSort(Action):

    ASCENDING: bool

    def __call__(self):
        columns = self.view.get_selected_columns()
        if len(columns) == 0:
            self.view.message_box_error(msg='Please select a column')
        elif len(columns) == 1:
            self.model.sort_dataframe(by=columns[0], ascending=self.ASCENDING)
            self.view.refresh_table()
        else:
            self.view.message_box_error(msg='Please select only one column')


class ActionSortAscending(ActionSort):

    ASCENDING = True


class ActionSortDescending(ActionSort):

    ASCENDING = False


class ActionDeleteSelectedRows(Action):

    def __call__(self):
        rows = self.view.get_selected_rows()
        if len(rows) == 0:
            return
        if self.view.message_box_yes_no(msg='Are you sure you want to delete the selected rows?'):
            self.model.drop(rows=rows)
            self.view.refresh_table()


class ActionResetTable(Action):

    def __call__(self):
        if len(self.model.dataframe) == 0:
            return  # nothing to reset

        if self.view.message_box_yes_no(msg='Are you sure you want to reset the table?'):
            self.model.reset_dataframe()
            self.view.refresh_table()


class ActionCopySelectedFastqFiles(Action):

    seq_ids: List[str]
    lab_sample_ids: List[str]
    fq_dir: str
    dst_dir: str
    in_r1_suffix: str
    in_r2_suffix: str
    out_r1_suffix: str
    out_r2_suffix: str

    def __call__(self):
        self.set_seq_ids_and_lab_sample_ids()
        if len(self.seq_ids) == 0:
            self.view.message_box_error('No rows selected')
            return

        self.set_fq_dir()
        if self.fq_dir == '':
            return

        self.set_in_r1_r2_suffix()
        if self.in_r1_suffix == '' or self.in_r2_suffix == '':
            return

        self.set_dst_dir()
        if self.dst_dir == '':
            return

        self.set_out_r1_r2_suffix()
        if self.out_r1_suffix == '' or self.out_r2_suffix == '':
            return

        for seq_id, lab_sample_id in zip(self.seq_ids, self.lab_sample_ids):
            self.copy_paired_fastq(seq_id=seq_id, lab_sample_id=lab_sample_id)

    def set_seq_ids_and_lab_sample_ids(self):
        rows = self.view.get_selected_rows()
        self.seq_ids = self.model.dataframe.loc[rows, 'ID'].tolist()
        self.lab_sample_ids = self.model.dataframe.loc[rows, 'Lab Sample ID'].tolist()

    def set_fq_dir(self):
        self.fq_dir = self.view.file_dialog_open_directory(caption='Select Directory Containing Fastq Files')

    def set_dst_dir(self):
        self.dst_dir = self.view.file_dialog_open_directory(caption='Select Destination Directory')

    def set_in_r1_r2_suffix(self):
        self.in_r1_suffix, self.in_r2_suffix = self.view.dialog_input_read1_read2_suffix()

    def set_out_r1_r2_suffix(self):
        self.out_r1_suffix, self.out_r2_suffix = self.view.dialog_output_read1_read2_suffix()

    def copy_paired_fastq(self, seq_id: str, lab_sample_id: str):
        fq1 = self.__get_src_fastq(lab_sample_id=lab_sample_id, suffix=self.in_r1_suffix)
        fq2 = self.__get_src_fastq(lab_sample_id=lab_sample_id, suffix=self.in_r2_suffix)

        if fq1 == '' or fq2 == '':
            self.view.message_box_error(f'Skip {seq_id} due to missing or multiple Fastq files for {lab_sample_id}')
            return

        self.__copy(src=fq1, dst=f'{self.dst_dir}/{seq_id}{self.out_r1_suffix}')
        self.__copy(src=fq2, dst=f'{self.dst_dir}/{seq_id}{self.out_r2_suffix}')

    def __get_src_fastq(self, lab_sample_id: str, suffix: str) -> str:
        files = get_files(
            source=self.fq_dir,
            startswith=lab_sample_id,
            endswith=suffix,
            isfullpath=True
        )
        if len(files) == 0:
            self.view.message_box_error(f'No Fastq file found for {lab_sample_id}*{suffix}')
            return ''
        elif len(files) > 1:
            self.view.message_box_error(f'Multiple Fastq files found for {lab_sample_id}*{suffix}: {files}')
            return ''
        else:
            return files[0]

    def __copy(self, src: str, dst: str):

        if not exists(src):
            self.view.message_box_error(f'The source file "{basename(src)}" does not exist')
            return

        if exists(dst):
            self.view.message_box_error(f'The destination file "{basename(dst)}" already exists, skip')
            return

        print(f'Copying {src} -> {dst}', flush=True)
        shutil.copyfile(src=src, dst=dst)

        if not md5(src) == md5(dst):
            self.view.message_box_error(f'Copy failed for {basename(src)}, delete "{basename(dst)}"')
            shutil.rmtree(dst)


def md5(file_path: str, buffer_size: int = 8192) -> str:
    """
    Compute the MD5 hash of a file. Written by ChatGPT.

    Args:
    - file_path (str): Path to the file.
    - buffer_size (int, optional): Size of the buffer to read in bytes. Default is 8192.

    Returns:
    - str: MD5 hash of the file.
    """
    md5_hash = hashlib.md5()

    with open(file_path, 'rb') as f:
        # Read the file in chunks
        for chunk in iter(lambda: f.read(buffer_size), b''):
            md5_hash.update(chunk)

    return md5_hash.hexdigest()


class ActionBuildRunTable(Action):

    def __call__(self):
        rows = self.view.get_selected_rows()
        seq_ids = self.model.dataframe.loc[rows, 'ID'].tolist()
        if len(seq_ids) == 0:
            self.view.message_box_error('No rows selected')
            return

        r1_suffix, r2_suffix = self.view.dialog_input_read1_read2_suffix()
        if r1_suffix == '' or r2_suffix == '':
            return

        sequencing_batch_table_file = self.view.file_dialog_open_table(caption='Open Sequencing Batch Table')
        if sequencing_batch_table_file == '':
            return

        fastq_correction_file = self.view.file_dialog_open_txt(caption='Open Fastq Correction File (Not Required)')

        output_file = self.view.file_dialog_save_table(filename='run_table.csv')
        if output_file == '':
            return

        use_lab_sample_id = self.view.message_box_yes_no(msg='Use Lab Sample ID instead of ID?')

        self.model.build_run_table(
            seq_ids=seq_ids,
            r1_suffix=r1_suffix,
            r2_suffix=r2_suffix,
            sequencing_batch_table_file=sequencing_batch_table_file,
            fastq_correction_file=fastq_correction_file,
            output_file=output_file,
            use_lab_sample_id=use_lab_sample_id)

        self.view.message_box_info(msg='Run table build complete')


class ActionFillInCellValues(Action):

    def __call__(self):

        selected_cells = self.view.get_selected_cells()
        if len(selected_cells) == 0:
            self.view.message_box_error('No cells selected')
            return

        value = self.view.dialog_fill_in_cell_values()
        if value == '':
            return

        try:
            self.model.fill_in_cell_values(cells=selected_cells, value=value)
            self.view.refresh_table()
        except Exception as e:
            self.view.message_box_error(msg=repr(e))


class ActionUndo(Action):

    def __call__(self):
        try:
            self.model.undo()
            self.view.refresh_table()
        except Exception as e:
            self.view.message_box_error(msg=repr(e))


class ActionRedo(Action):

    def __call__(self):
        try:
            self.model.redo()
            self.view.refresh_table()
        except Exception as e:
            self.view.message_box_error(msg=repr(e))
