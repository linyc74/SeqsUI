import os
import unittest
import pandas as pd


class TestCase(unittest.TestCase):

    def set_up(self, py_path: str):
        self.indir = os.path.relpath(path=py_path[:-3], start=os.getcwd())

    def assertDataFrameEqual(self, first: pd.DataFrame, second: pd.DataFrame):
        self.assertListEqual(list(first.columns), list(second.columns))
        self.assertListEqual(list(first.index), list(second.index))
        for c in first.columns:
            for i in first.index:
                a, b = first.loc[i, c], second.loc[i, c]
                if pd.isna(a) and pd.isna(b):
                    continue
                self.assertAlmostEqual(a, b)
