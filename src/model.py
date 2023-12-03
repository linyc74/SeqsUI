import pandas as pd
from datetime import date
from os.path import basename
from typing import Tuple, List, Optional


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
    'Primary': '02',
    'Primary Tumor': '02',
    'Precancer': '03',
    'Recurrent': '04',
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
] + IMPORT_COLUMNS


class Model:

    dataframe: pd.DataFrame  # this is the main sequencing table

    def __init__(self):
        self.reset_dataframe()

    def reset_dataframe(self):
        self.dataframe = pd.DataFrame(columns=SEQUENCING_TABLE_COLUMNS)

    def read_sequencing_table(self, file: str):
        self.dataframe = ReadTable().main(file=file, columns=SEQUENCING_TABLE_COLUMNS)

    def save_sequencing_table(self, file: str):
        if file.endswith('.xlsx'):
            self.dataframe.to_excel(file, index=False)
        else:
            self.dataframe.to_csv(file, index=False)

    def get_dataframe(self) -> pd.DataFrame:
        return self.dataframe.copy()

    def sort_dataframe(self, by: str, ascending: bool):
        self.dataframe = self.dataframe.sort_values(
            by=by,
            ascending=ascending,
            kind='mergesort'  # deterministic, keep the original order when tied
        ).reset_index(
            drop=True
        )

    def drop(self, rows: Optional[List[int]] = None, columns: Optional[List[str]] = None):
        self.dataframe = self.dataframe.drop(
            index=rows,
            columns=columns
        ).reset_index(
            drop=True
        )

    def import_new_entries(self, file: str):
        dataframe = self.dataframe.copy()
        new_entry_df = ReadTable().main(file=file, columns=IMPORT_COLUMNS)

        for i, in_row in new_entry_df.iterrows():

            out_row = GenerateSequencingTableRow().main(
                dataframe=dataframe,
                in_row=in_row)

            dataframe = append(dataframe, out_row)

        # update self.dataframe only after all rows succeed
        self.dataframe = dataframe

    def build_run_table(
            self,
            seq_ids: List[str],
            r1_suffix: str,
            r2_suffix: str,
            bed_file: str,
            output_file: str):

        return BuildRunTable().main(
            seq_df=self.dataframe,
            seq_ids=seq_ids,
            r1_suffix=r1_suffix,
            r2_suffix=r2_suffix,
            bed_file=bed_file,
            output_file=output_file)


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
        self.convert_datetime_columns()

        return self.df

    def read_file(self):
        self.df = pd.read_excel(self.file) if self.file.endswith('.xlsx') else pd.read_csv(self.file)

    def assert_columns(self):
        assert set(self.columns) == set(self.df.columns), \
            f'Columns in "{basename(self.file)}": {self.df.columns.tolist()} do not match the expected columns: {self.columns}'

    def convert_datetime_columns(self):
        for c in self.df.columns:
            if c.endswith('Date'):
                self.df[c] = pd.to_datetime(self.df[c])


class GenerateSequencingTableRow:

    dataframe: pd.DataFrame
    in_row: pd.Series

    patient_id: int
    patient_sequencing_number: int
    seq_id: str

    out_row: pd.Series

    def main(
            self,
            dataframe: pd.DataFrame,
            in_row: pd.Series) -> pd.Series:

        self.dataframe = dataframe.copy()
        self.in_row = in_row.copy()

        self.set_patient_id()
        self.set_patient_sequencing_number()
        self.set_seq_id()
        self.set_out_row()

        return self.out_row

    def set_patient_id(self):
        if len(self.dataframe) == 0:  # empty sequencing table
            self.patient_id = 1
            return

        a = self.dataframe[LAB] == self.in_row[LAB]
        b = self.dataframe[LAB_PATIENT_ID] == self.in_row[LAB_PATIENT_ID]
        is_existing_patient = a & b

        if any(is_existing_patient):
            self.patient_id = self.dataframe.loc[is_existing_patient, PATIENT_ID].iloc[0]
        else:
            self.patient_id = self.dataframe[PATIENT_ID].max() + 1

    def set_patient_sequencing_number(self):
        self.patient_sequencing_number = (self.dataframe[PATIENT_ID] == self.patient_id).sum() + 1

    def set_seq_id(self):
        a = HOSPITAL_RESEARCH_CENTER_TO_CODE[self.in_row[HOSPITAL_RESEARCH_CENTER]]
        b = f'{self.patient_id:05d}'
        c = CANCER_TYPE_TO_CODE[self.in_row[CANCER_TYPE]]
        d = TISSUE_TYPE_TO_CODE[self.in_row[TISSUE_TYPE]]
        e = SEQUENCING_TYPE_TO_CODE[self.in_row[SEQUENCING_TYPE]]
        f = f'{self.in_row[VIAL_SEQUENCING_NUMBER]:02d}'
        g = f'{self.patient_sequencing_number:02d}'
        self.seq_id = f'{a}-{b}-{c}{d}-{e}-{self.in_row[VIAL]}{f}-{g}'

    def set_out_row(self):
        self.out_row = pd.Series({
            ID: self.seq_id,
            PATIENT_ID: self.patient_id,
            PATIENT_SEQUENCING_NUMBER: self.patient_sequencing_number,
            IMPORT_DATE: date.today(),
        })
        for c in IMPORT_COLUMNS:
            self.out_row[c] = self.in_row[c]


class BuildRunTable:

    seq_df: pd.DataFrame
    seq_ids: List[str]
    r1_suffix: str
    r2_suffix: str
    bed_file: str
    output_file: str

    tumor_ids: List[str]
    normal_ids: List[str]

    run_df: pd.DataFrame

    def main(
            self,
            seq_df: pd.DataFrame,
            seq_ids: List[str],
            r1_suffix: str,
            r2_suffix: str,
            bed_file: str,
            output_file: str):

        self.seq_df = seq_df.copy()
        self.seq_ids = seq_ids
        self.r1_suffix = r1_suffix
        self.r2_suffix = r2_suffix
        self.bed_file = bed_file
        self.output_file = output_file

        self.subset_seq_df()
        self.set_tumor_ids()
        self.set_normal_ids()

        self.run_df = pd.DataFrame()
        for seq_id in self.tumor_ids:
            self.generate_one_row(tumor_id=seq_id)
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

    def generate_one_row(self, tumor_id: str):
        r1, r2 = self.r1_suffix, self.r2_suffix
        normal_id = self.get_matched_normal_id(tumor_id=tumor_id)
        row = pd.Series({
            'Tumor Fastq R1': f'{tumor_id}{r1}',
            'Tumor Fastq R2': f'{tumor_id}{r2}',
            'Normal Fastq R1': f'{normal_id}{r1}' if normal_id is not None else '',
            'Normal Fastq R2': f'{normal_id}{r2}' if normal_id is not None else '',
            'Output Name': tumor_id,
            'BED File': self.bed_file,
        })
        self.run_df = append(self.run_df, row)

    def get_matched_normal_id(self, tumor_id: str) -> Optional[str]:
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

    def save_output_file(self):
        if self.output_file.endswith('.xlsx'):
            self.run_df.to_excel(self.output_file, index=False)
        else:
            self.run_df.to_csv(self.output_file, index=False)


def append(df: pd.DataFrame, s: pd.Series) -> pd.DataFrame:
    return pd.concat([df, pd.DataFrame([s])], ignore_index=True)
