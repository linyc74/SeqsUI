import pandas as pd
from src.model import Model, BuildRunTable
from .setup import TestCase


class TestModel(TestCase):

    def setUp(self):
        self.set_up(py_path=__file__)

    def tearDown(self):
        self.tear_down()

    def test_import_first_patient(self):
        model = Model()
        model.import_new_entries(file=f'{self.indir}/new-patient.csv')

    def test_import_existing_patient(self):
        model = Model()
        model.read_sequencing_table(file=f'{self.indir}/sequencing-table.csv')

        model.import_new_entries(file=f'{self.indir}/existing-patient.csv')
        actual = model.dataframe['ID'].tolist()
        expected = [
            '001-00001-0101-E-X01-01',
            '001-00001-0101-E-X02-02',
            '001-00001-0102-E-X01-03',
        ]
        self.assertListEqual(expected, actual)

    def test_import_new_patient(self):
        model = Model()
        model.read_sequencing_table(file=f'{self.indir}/sequencing-table.csv')

        model.import_new_entries(file=f'{self.indir}/new-patient.csv')
        actual = model.dataframe['ID'].tolist()
        expected = [
            '001-00001-0101-E-X01-01',
            '001-00002-0101-E-X01-01',
            '001-00003-0102-E-X01-01',
        ]
        self.assertListEqual(expected, actual)

    def test_read_wrong_sequencing_table(self):
        model = Model()
        with self.assertRaises(AssertionError):
            model.read_sequencing_table(file=f'{self.indir}/wrong.csv')

    def test_import_wrong_sequencing_entries(self):
        model = Model()
        with self.assertRaises(AssertionError):
            model.import_new_entries(file=f'{self.indir}/wrong.csv')


class TestBuildRunTable(TestCase):

    def setUp(self):
        self.set_up(py_path=__file__)

    def tearDown(self):
        self.tear_down()

    def test_main(self):
        seq_df = pd.read_csv(f'{self.indir}/seq-df.csv')
        seq_ids = [
            '002-00002-0101-E-X01-01',
            '002-00002-0101-E-X01-99',
            '002-00002-0103-E-X01-02',
            '002-00002-0102-E-X01-03',
            '002-00003-0102-E-X01-03',
        ]
        BuildRunTable().main(
            seq_df=seq_df,
            seq_ids=seq_ids,
            r1_suffix='_R1.fastq.gz',
            r2_suffix='_R2.fastq.gz',
            bed_file='bed_file.bed',
            output_file=f'{self.outdir}/run-table.csv',
        )
        self.assertDataFrameEqual(
            first=pd.read_csv(f'{self.outdir}/run-table.csv'),
            second=pd.read_csv(f'{self.indir}/run-table.csv'),
        )
