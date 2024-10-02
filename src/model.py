import pandas as pd
from datetime import date
from os.path import basename
from typing import List, Optional, Tuple, Any


HOSPITAL_RESEARCH_CENTER_TO_CODE = {
    '台北榮總': '001',
    'Taipei Veterans General Hospital': '001',
    '宜蘭附醫': '002',
    'National Yang Ming Chiao Tung University Hospital': '002',
}
CANCER_TYPE_TO_CODE = {
    'HNSCC': '01',
}
TISSUE_TYPE_TO_CODE = {
    'Normal': '01',
    'Adjacent Normal': '01',
    'Tumor': '02',
    'Primary': '02',
    'Primary Tumor': '02',
    'Precancer': '03',
    'Recurrent': '07',
    'Recurrent Tumor': '07',
}
SEQUENCING_TYPE_TO_CODE = {
    'WES': 'E',
    'Exome Sequencing': 'E',
    'Whole Exome Sequencing': 'E',
    'RNA-seq': 'R',
}


ID = 'ID'
PATIENT_ID = 'Patient ID'
PATIENT_SEQUENCING_NUMBER = 'Patient Sequencing Number'
IMPORT_DATE = 'Import Date'
HOSPITAL_RESEARCH_CENTER = 'Hospital Research Center'
LAB = 'Lab'
LAB_PATIENT_ID = 'Lab Patient ID'
LAB_SAMPLE_ID = 'Lab Sample ID'
CANCER_TYPE = 'Cancer Type'
TISSUE_TYPE = 'Tissue Type'
SEQUENCING_TYPE = 'Sequencing Type'
VIAL = 'Vial'
VIAL_SEQUENCING_NUMBER = 'Vial Sequencing Number'
SEQUENCING_BATCH_ID = 'Sequencing Batch ID'


IMPORT_COLUMNS = [
    HOSPITAL_RESEARCH_CENTER,
    LAB,
    LAB_PATIENT_ID,
    LAB_SAMPLE_ID,
    CANCER_TYPE,
    TISSUE_TYPE,
    SEQUENCING_TYPE,
    VIAL,
    VIAL_SEQUENCING_NUMBER,
]
SEQUENCING_TABLE_COLUMNS = [
    ID,
    PATIENT_ID,
    PATIENT_SEQUENCING_NUMBER,
    IMPORT_DATE,
    HOSPITAL_RESEARCH_CENTER,
    LAB,
    LAB_PATIENT_ID,
    LAB_SAMPLE_ID,
    CANCER_TYPE,
    TISSUE_TYPE,
    SEQUENCING_TYPE,
    VIAL,
    VIAL_SEQUENCING_NUMBER,
    SEQUENCING_BATCH_ID,
]


class Model:

    MAX_UNDO = 100

    dataframe: pd.DataFrame  # this is the main sequencing table

    undo_cache: List[pd.DataFrame]
    redo_cache: List[pd.DataFrame]

    def __init__(self):
        self.dataframe = pd.DataFrame(columns=SEQUENCING_TABLE_COLUMNS)
        self.undo_cache = []
        self.redo_cache = []

    def undo(self):
        if len(self.undo_cache) == 0:
            return
        self.redo_cache.append(self.dataframe)
        self.dataframe = self.undo_cache.pop()

    def redo(self):
        if len(self.redo_cache) == 0:
            return
        self.undo_cache.append(self.dataframe)
        self.dataframe = self.redo_cache.pop()

    def __add_to_undo_cache(self):
        self.undo_cache.append(self.dataframe.copy())
        if len(self.undo_cache) > self.MAX_UNDO:
            self.undo_cache.pop(0)
        self.redo_cache = []  # clear redo cache

    def reset_dataframe(self):
        new = pd.DataFrame(columns=SEQUENCING_TABLE_COLUMNS)
        self.__add_to_undo_cache()
        self.dataframe = new

    def read_sequencing_table(self, file: str):
        new = ReadTable().main(file=file, columns=SEQUENCING_TABLE_COLUMNS)
        self.__add_to_undo_cache()
        self.dataframe = new

    def save_sequencing_table(self, file: str):
        if file.endswith('.xlsx'):
            self.dataframe.to_excel(file, index=False)
        else:
            self.dataframe.to_csv(file, index=False)

    def get_dataframe(self) -> pd.DataFrame:
        return self.dataframe.copy()

    def sort_dataframe(self, by: str, ascending: bool):
        new = self.dataframe.sort_values(
            by=by,
            ascending=ascending,
            kind='mergesort'  # deterministic, keep the original order when tied
        ).reset_index(
            drop=True
        )
        self.__add_to_undo_cache()
        self.dataframe = new

    def drop(self, rows: Optional[List[int]] = None, columns: Optional[List[str]] = None):
        new = self.dataframe.drop(
            index=rows,
            columns=columns
        ).reset_index(
            drop=True
        )
        self.__add_to_undo_cache()
        self.dataframe = new

    def import_patient_sample_sheet(self, file: str):
        dataframe = self.dataframe.copy()

        patient_sample_df = ReadTable().main(file=file, columns=IMPORT_COLUMNS)

        for i, in_row in patient_sample_df.iterrows():

            out_row = GenerateSequencingTableRow().main(
                dataframe=dataframe,
                in_row=in_row)

            if out_row is not None:
                dataframe = append(dataframe, out_row)

        # update self.dataframe only after all rows succeed
        self.__add_to_undo_cache()
        self.dataframe = dataframe

    def fill_in_cell_values(self, cells: List[Tuple[int, str]], value: Any):
        new = self.dataframe.copy()
        for idx, column in cells:
            new.loc[idx, column] = value

        # update self.dataframe only after all cells succeed
        self.__add_to_undo_cache()
        self.dataframe = new

    def build_run_table(
            self,
            seq_ids: List[str],
            r1_suffix: str,
            r2_suffix: str,
            sequencing_batch_table_file: str,
            fastq_correction_file: str,
            output_file: str,
            use_lab_sample_id: bool):

        return BuildRunTable().main(
            seq_df=self.dataframe,
            seq_ids=seq_ids,
            r1_suffix=r1_suffix,
            r2_suffix=r2_suffix,
            sequencing_batch_table_file=sequencing_batch_table_file,
            fastq_correction_file=fastq_correction_file,
            output_file=output_file,
            use_lab_sample_id=use_lab_sample_id)


class ReadTable:

    file: str
    columns: List[str]

    df: pd.DataFrame

    def main(
            self,
            file: str,
            columns: List[str]) -> pd.DataFrame:

        self.file = file
        self.columns = columns

        self.read_file()
        self.assert_columns()
        self.df = self.df[self.columns]
        self.df.dropna(how='all', inplace=True)

        return self.df

    def read_file(self):
        if self.file.endswith('.xlsx'):
            self.df = pd.read_excel(self.file)
        elif self.file.endswith('.csv'):
            self.df = pd.read_csv(self.file)
        else:
            raise ValueError(f'File "{self.file}" must be .xlsx or .csv')

    def assert_columns(self):
        for c in self.columns:
            assert c in self.df.columns, f'Column "{c}" not found in "{basename(self.file)}"'


class GenerateSequencingTableRow:

    dataframe: pd.DataFrame
    in_row: pd.Series

    not_sequenced: bool
    existing_patient: bool
    existing_sample: bool
    patient_id: int
    patient_sequencing_number: int
    seq_id: str

    out_row: pd.Series

    def main(
            self,
            dataframe: pd.DataFrame,
            in_row: pd.Series) -> Optional[pd.Series]:

        self.dataframe = dataframe.copy()
        self.in_row = in_row.copy()

        self.assert_no_nan()
        self.tell_if_patient_or_sample_exist()

        if self.existing_sample:
            return None

        self.cast_datatype()
        self.set_patient_id()
        self.set_patient_sequencing_number()
        self.set_seq_id()
        self.set_out_row()

        return self.out_row

    def assert_no_nan(self):
        for key in [
            HOSPITAL_RESEARCH_CENTER,
            LAB,             #
            LAB_PATIENT_ID,  # these three are required to identify a patient and a sample
            LAB_SAMPLE_ID,   #
            CANCER_TYPE,
            TISSUE_TYPE,
            SEQUENCING_TYPE,
            VIAL,
            VIAL_SEQUENCING_NUMBER
        ]:
            assert pd.notna(self.in_row[key]), f'Lab Sample ID "{self.in_row[LAB_SAMPLE_ID]}": "{key}" is empty.'

    def tell_if_patient_or_sample_exist(self):
        a = self.dataframe[LAB] == self.in_row[LAB]
        b = self.dataframe[LAB_PATIENT_ID] == self.in_row[LAB_PATIENT_ID]
        c = self.dataframe[LAB_SAMPLE_ID] == self.in_row[LAB_SAMPLE_ID]

        self.existing_patient = any(a & b)
        self.existing_sample = any(a & b & c)

    def cast_datatype(self):
        self.in_row[VIAL_SEQUENCING_NUMBER] = int(self.in_row[VIAL_SEQUENCING_NUMBER])

    def set_patient_id(self):
        if len(self.dataframe) == 0:  # empty sequencing table
            self.patient_id = 1
            return

        if self.existing_patient:
            self.patient_id = self.__get_existing_patient_id()
        else:
            self.patient_id = self.dataframe[PATIENT_ID].max() + 1

    def __get_existing_patient_id(self):
        a = self.dataframe[LAB] == self.in_row[LAB]
        b = self.dataframe[LAB_PATIENT_ID] == self.in_row[LAB_PATIENT_ID]
        return self.dataframe.loc[a & b, PATIENT_ID].iloc[0]

    def set_patient_sequencing_number(self):
        self.patient_sequencing_number = (self.dataframe[PATIENT_ID] == self.patient_id).sum() + 1

    def set_seq_id(self):
        a = HOSPITAL_RESEARCH_CENTER_TO_CODE[self.in_row[HOSPITAL_RESEARCH_CENTER]]
        b = f'{self.patient_id:05d}'
        c = CANCER_TYPE_TO_CODE[self.in_row[CANCER_TYPE]]
        d = TISSUE_TYPE_TO_CODE[self.in_row[TISSUE_TYPE]]
        e = SEQUENCING_TYPE_TO_CODE[self.in_row[SEQUENCING_TYPE]]
        f = f'{self.in_row[VIAL_SEQUENCING_NUMBER]:02d}'  # sometimes vial sequencing number can be float because of nan
        g = f'{self.patient_sequencing_number:02d}'
        self.seq_id = f'{a}-{b}-{c}{d}-{e}-{self.in_row[VIAL]}{f}-{g}'

    def set_out_row(self):
        self.out_row = pd.Series({
            ID: self.seq_id,
            PATIENT_ID: self.patient_id,
            PATIENT_SEQUENCING_NUMBER: self.patient_sequencing_number,
            IMPORT_DATE: date.today(),
        })
        common_columns = set(IMPORT_COLUMNS).intersection(SEQUENCING_TABLE_COLUMNS)
        for c in common_columns:
            self.out_row[c] = self.in_row[c]


class BuildRunTable:

    seq_df: pd.DataFrame
    seq_ids: List[str]
    r1_suffix: str
    r2_suffix: str
    sequencing_batch_table_file: str
    fastq_correction_file: str
    output_file: str
    use_lab_sample_id: bool

    tumor_ids: List[str]
    normal_ids: List[str]
    correct_fastqs: List[str]

    run_df: pd.DataFrame

    def main(
            self,
            seq_df: pd.DataFrame,
            seq_ids: List[str],
            r1_suffix: str,
            r2_suffix: str,
            sequencing_batch_table_file: str,
            fastq_correction_file: str,
            output_file: str,
            use_lab_sample_id: bool):

        self.seq_df = seq_df.copy()
        self.seq_ids = seq_ids
        self.r1_suffix = r1_suffix
        self.r2_suffix = r2_suffix
        self.sequencing_batch_table_file = sequencing_batch_table_file
        self.fastq_correction_file = fastq_correction_file
        self.output_file = output_file
        self.use_lab_sample_id = use_lab_sample_id

        self.subset_seq_df()
        self.set_tumor_ids()
        self.set_normal_ids()
        self.set_correct_fastqs()

        self.run_df = pd.DataFrame()
        for tumor_id in self.tumor_ids:
            self.generate_one_row(tumor_id=tumor_id)
        self.save_output_file()

    def subset_seq_df(self):
        self.seq_df = self.seq_df[self.seq_df[ID].isin(self.seq_ids)]

    def set_tumor_ids(self):
        not_normal = self.seq_df[TISSUE_TYPE] != 'Normal'
        self.tumor_ids = self.seq_df.loc[not_normal, ID].tolist()

    def set_normal_ids(self):
        normal_df = self.seq_df[self.seq_df[TISSUE_TYPE] == 'Normal']

        normal_df = normal_df.sort_values(
            by=PATIENT_SEQUENCING_NUMBER,  # by highest (i.e. latest) sequencing number
            ascending=False
        ).drop_duplicates(
            subset=[PATIENT_ID, TISSUE_TYPE],  # each patient can only have one normal sample
            keep='first'
        )

        self.normal_ids = normal_df[ID].tolist()

    def set_correct_fastqs(self):
        if self.fastq_correction_file == '':
            self.correct_fastqs = []
            return

        with open(self.fastq_correction_file) as fh:
            text = fh.read()
        self.correct_fastqs = []
        text = text.replace('\t', ' ').replace('\n', ' ')
        for item in text.split(' '):
            if item != '':
                self.correct_fastqs.append(item)

    def generate_one_row(self, tumor_id: str):
        normal_id = self.__get_matched_normal_id(tumor_id=tumor_id)
        sequencing_batch_id = self.__get_sequencing_batch_id(seq_id=tumor_id)
        bed_file = self.__get_bed_file(seq_id=tumor_id)

        if bed_file == '':
            print(f'WARNING: BED file not found for "{tumor_id}"', flush=True)

        if self.use_lab_sample_id:
            tumor_id = self.__get_lab_sample_id(sample_id=tumor_id)
            if normal_id is not None:
                normal_id = self.__get_lab_sample_id(sample_id=normal_id)

        tumor_fq1 = self.__get_correct_fastq(prefix=tumor_id, suffix=self.r1_suffix)
        tumor_fq2 = self.__get_correct_fastq(prefix=tumor_id, suffix=self.r2_suffix)
        if normal_id is not None:
            normal_fq1 = self.__get_correct_fastq(prefix=normal_id, suffix=self.r1_suffix)
            normal_fq2 = self.__get_correct_fastq(prefix=normal_id, suffix=self.r2_suffix)
        else:
            normal_id, normal_fq1, normal_fq2 = '', '', ''

        row = pd.Series({
            'Tumor Sample Name': tumor_id,
            'Tumor Fastq R1': tumor_fq1,
            'Tumor Fastq R2': tumor_fq2,
            'Normal Sample Name': normal_id,
            'Normal Fastq R1': normal_fq1,
            'Normal Fastq R2': normal_fq2,
            'Output Name': tumor_id,
            'Sequencing Batch ID': sequencing_batch_id,
            'BED File': bed_file,
        })

        self.run_df = append(self.run_df, row)

    def __get_matched_normal_id(self, tumor_id: str) -> Optional[str]:
        """
        Example:
            If tumor_id is                   '001-00001-0102-E-X01-02'
            then normal_id should start with '001-00001-0101'
        """
        matched_normal_prefix = tumor_id[:12] + '01'
        for seq_id in self.normal_ids:
            if seq_id.startswith(matched_normal_prefix):
                return seq_id
        return None

    def __get_sequencing_batch_id(self, seq_id: str) -> str:
        return self.seq_df.loc[self.seq_df[ID] == seq_id, SEQUENCING_BATCH_ID].iloc[0]

    def __get_bed_file(self, seq_id: str) -> str:
        sequencing_batch_id = self.seq_df.loc[self.seq_df[ID] == seq_id, SEQUENCING_BATCH_ID].iloc[0]

        seq_batch_df = ReadTable().main(
            file=self.sequencing_batch_table_file,
            columns=['ID', 'BED File']
        ).set_index('ID')

        sequencing_batch_id_to_bed_file = seq_batch_df['BED File'].to_dict()

        return sequencing_batch_id_to_bed_file.get(sequencing_batch_id, '')

    def __get_lab_sample_id(self, sample_id: str) -> str:
        df = self.seq_df
        lab_sample_ids = df.loc[df[ID] == sample_id, LAB_SAMPLE_ID].to_list()
        assert len(lab_sample_ids) == 1, f'More than one Lab Sample ID were found for {sample_id}'
        return lab_sample_ids[0]

    def __get_correct_fastq(self, prefix: str, suffix: str) -> str:
        for f in self.correct_fastqs:
            if f.startswith(prefix) and f.endswith(suffix):
                return f
        return prefix + suffix

    def save_output_file(self):
        if self.output_file.endswith('.xlsx'):
            self.run_df.to_excel(self.output_file, index=False)
        else:
            self.run_df.to_csv(self.output_file, index=False)


def append(df: pd.DataFrame, s: pd.Series) -> pd.DataFrame:
    return pd.concat([df, pd.DataFrame([s])], ignore_index=True)
