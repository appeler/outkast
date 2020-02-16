#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for secc_caste_ln.py

"""

import os
import shutil
import unittest
import pandas as pd
from outkast import secc_caste
from . import capture


class TestInRollsFn(unittest.TestCase):

    def setUp(self):
        names = [{'name': 'patel'},
                 {'name': 'kohli'},
                 {'name': 'lal'},
                 {'name': 'agarwal'}]
        self.df = pd.DataFrame(names)

    def tearDown(self):
        pass

    def test_secc_caste_ln(self):
        odf = secc_caste(self.df, 'name')
        self.assertIn('prop_sc', odf.columns)
        self.assertTrue(odf.iloc[2].prop_sc > 0.3)


    def test_secc_caste_ln_state(self):
        odf = secc_caste(self.df, 'name', 'kerala')
        self.assertIn('prop_sc', odf.columns)
        self.assertTrue(odf.iloc[2].prop_sc > 0.1)

    def test_secc_caste_ln_state_year(self):
        odf = secc_caste(self.df, 'name', 'kerala', 1985)
        self.assertIn('prop_sc', odf.columns)
        self.assertTrue(odf.iloc[2].prop_sc > 0.1)


if __name__ == '__main__':
    unittest.main()
