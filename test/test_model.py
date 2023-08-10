from src.model import Model
from .setup import TestCase


class TestModel(TestCase):

    def setUp(self):
        self.set_up(py_path=__file__)

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
        actual, _ = model.read_sequencing_table(file=f'{self.indir}/wrong.csv')
        self.assertFalse(actual)

    def test_import_wrong_sequencing_entries(self):
        model = Model()
        actual, _ = model.import_new_entries(file=f'{self.indir}/wrong.csv')
        self.assertFalse(actual)
