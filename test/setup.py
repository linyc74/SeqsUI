import os
import shutil
import unittest
import pandas as pd
from os.path import relpath, dirname, join


class TestCase(unittest.TestCase):

    def set_up(self, py_path: str):
        self.indir = relpath(path=py_path[:-3], start=os.getcwd())
        basedir = dirname(self.indir)
        self.workdir = join(basedir, 'workdir')
        self.outdir = join(basedir, 'outdir')

        for d in [self.workdir, self.outdir]:
            os.makedirs(d, exist_ok=True)

    def tear_down(self):
        shutil.rmtree(self.workdir)
        shutil.rmtree(self.outdir)

    def assertDataFrameEqual(self, first: pd.DataFrame, second: pd.DataFrame):
        self.assertListEqual(list(first.columns), list(second.columns))
        self.assertListEqual(list(first.index), list(second.index))
        for c in first.columns:
            for i in first.index:
                a, b = first.loc[i, c], second.loc[i, c]
                if pd.isna(a) and pd.isna(b):
                    continue
                self.assertAlmostEqual(a, b)
