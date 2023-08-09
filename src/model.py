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

    def read_sequencing_table(self, csv: str) -> Tuple[bool, str]:
        df = pd.read_csv(csv)

        for c in SEQUENCING_TABLE_COLUMNS:
            if c not in df.columns:
                return False, f'Column "{c}" not found in "{basename(csv)}"'

        self.dataframe = df
        return True, ''

    def save_sequencing_table(self, csv: str):
        self.dataframe.to_csv(csv, index=False)

    def get_dataframe(self) -> pd.DataFrame:
        return self.dataframe.copy()

    def sort_dataframe(self, by: str, ascending: bool):
        self.dataframe = self.dataframe.sort_values(
            by=by,
            ascending=ascending,
            kind='mergesort'  # deterministic, keep the original order when tied
        )

    def drop(self, rows: Optional[List[int]] = None, columns: Optional[List[str]] = None):
        self.dataframe = self.dataframe.drop(
            index=rows,
            columns=columns
        ).reset_index(
            drop=True
        )

    def import_new_entries(self, csv: str) -> Tuple[bool, str]:
        df = pd.read_csv(csv)

        for c in IMPORT_COLUMNS:
            if c not in df.columns:
                return False, f'Column "{c}" not found in "{basename(csv)}"'

        for i, in_row in df.iterrows():

            row = GenerateSequencingTableRow().main(
                dataframe=self.dataframe,
                in_row=in_row)

            self.dataframe = append(self.dataframe, row)

        return True, ''


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


def append(df: pd.DataFrame, s: pd.Series) -> pd.DataFrame:
    return pd.concat([df, pd.DataFrame([s])], ignore_index=True)
