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
        model.import_patient_sample_sheet(file=f'{self.indir}/patient-sample-sheet-new-patient.csv')
        actual = model.dataframe['ID'].tolist()
        expected = [
            '001-00001-0101-E-X01-01',
        ]
        self.assertListEqual(expected, actual)
        self.assertEqual(1, len(model.undo_cache))

    def test_import_new_patient(self):
        model = Model()
        model.read_sequencing_table(file=f'{self.indir}/sequencing-table.csv')
        model.import_patient_sample_sheet(file=f'{self.indir}/patient-sample-sheet-new-patient.csv')
        actual = model.dataframe['ID'].tolist()
        expected = [
            '001-00001-0101-E-X01-01',
            '001-00002-0101-E-X01-01',
        ]
        self.assertListEqual(expected, actual)
        self.assertEqual(2, len(model.undo_cache))

    def test_import_existing_patient_new_sample(self):
        model = Model()
        model.read_sequencing_table(file=f'{self.indir}/sequencing-table.csv')
        model.import_patient_sample_sheet(file=f'{self.indir}/patient-sample-sheet-existing-patient-new-sample.csv')
        actual = model.dataframe['ID'].tolist()
        expected = [
            '001-00001-0101-E-X01-01',
            '001-00001-0101-R-A01-02',
        ]
        self.assertListEqual(expected, actual)
        self.assertEqual(2, len(model.undo_cache))

    def test_import_existing_sample(self):
        model = Model()
        model.read_sequencing_table(file=f'{self.indir}/sequencing-table.csv')
        model.import_patient_sample_sheet(file=f'{self.indir}/patient-sample-sheet-existing-sample.csv')
        actual = model.dataframe['ID'].tolist()
        expected = [
            '001-00001-0101-E-X01-01',
        ]
        self.assertListEqual(expected, actual)
        self.assertEqual(2, len(model.undo_cache))

    def test_import_nan_exception(self):
        model = Model()
        model.read_sequencing_table(file=f'{self.indir}/sequencing-table.csv')
        with self.assertRaises(AssertionError):
            model.import_patient_sample_sheet(file=f'{self.indir}/patient-sample-sheet-nan.csv')
        self.assertEqual(1, len(model.undo_cache))

    def test_undo(self):
        model = Model()
        model.read_sequencing_table(file=f'{self.indir}/sequencing-table.csv')
        model.undo()
        self.assertEqual(0, len(model.dataframe))

    def test_redo(self):
        model = Model()
        model.read_sequencing_table(file=f'{self.indir}/sequencing-table.csv')
        model.undo()
        model.redo()
        self.assertEqual(1, len(model.dataframe))

    def test_fill_in_cell_values(self):
        model = Model()
        model.read_sequencing_table(file=f'{self.indir}/sequencing-table.csv')
        model.fill_in_cell_values(cells=[(0, 'Patient ID')], value=1000)
        self.assertEqual(1000, model.dataframe.loc[0, 'Patient ID'])
        self.assertEqual(2, len(model.undo_cache))


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
            sequencing_batch_table_file=f'{self.indir}/sequencing-batch-table.csv',
            fastq_correction_file='',
            output_file=f'{self.outdir}/run-table.csv',
            use_lab_sample_id=True,
        )
        self.assertDataFrameEqual(
            first=pd.read_csv(f'{self.outdir}/run-table.csv'),
            second=pd.read_csv(f'{self.indir}/run-table.csv'),
        )

    def test_tumor_only(self):
        seq_df = pd.read_csv(f'{self.indir}/seq-df.csv')
        seq_ids = [
            '002-00002-0103-E-X01-02',
            '002-00002-0102-E-X01-03',
            '002-00003-0102-E-X01-03',
        ]
        BuildRunTable().main(
            seq_df=seq_df,
            seq_ids=seq_ids,
            r1_suffix='_R1.fastq.gz',
            r2_suffix='_R2.fastq.gz',
            sequencing_batch_table_file=f'{self.indir}/sequencing-batch-table.csv',
            fastq_correction_file='',
            output_file=f'{self.outdir}/run-table.csv',
            use_lab_sample_id=True,
        )
        self.assertDataFrameEqual(
            first=pd.read_csv(f'{self.outdir}/run-table.csv'),
            second=pd.read_csv(f'{self.indir}/run-table-tumor-only.csv'),
        )

    def test_fastq_correction(self):
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
            sequencing_batch_table_file=f'{self.indir}/sequencing-batch-table.csv',
            fastq_correction_file=f'{self.indir}/md5sum.txt',
            output_file=f'{self.outdir}/run-table.csv',
            use_lab_sample_id=True,
        )
        self.assertDataFrameEqual(
            first=pd.read_csv(f'{self.outdir}/run-table.csv'),
            second=pd.read_csv(f'{self.indir}/run-table-fastq-correction.csv'),
        )
