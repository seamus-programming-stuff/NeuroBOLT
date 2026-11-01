"""Synthetic tests for scientific failure modes; never inspect real outcomes."""
from pathlib import Path
import unittest

import numpy as np
from interp_next_analysis import (metric, fdr, person, schema_features,
    bootstrap_means, signflip, cyclic_null, TR, folds)


class ContinuationTests(unittest.TestCase):
    def test_correlation_does_not_imply_raw_R2(self):
        y=np.linspace(-1,1,121);y=y/y.std()
        m=metric(.2*y+1,y)
        self.assertAlmostEqual(m['r'],1)
        self.assertAlmostEqual(m['R2'],-.64)

    def test_nonzero_constant_prediction_is_undefined_r(self):
        y=np.linspace(-1,1,133)
        for value in (0,1/3,1234.56):
            m=metric(np.full_like(y,value),y)
            self.assertTrue(np.isnan(m['r']))
            self.assertEqual(m['SD_ratio'],0)

    def test_semantic_EEG_schema_excludes_target_and_wrong_width(self):
        ch=['E'+str(i) for i in range(26)]
        self.assertEqual(schema_features(np.zeros((3,13728)),ch).shape,(3,26,44,12))
        for bad in (ch[:-1],ch[:-1]+['global signal clean']):
            with self.assertRaises(AssertionError):schema_features(np.zeros((3,13728)),bad)
        with self.assertRaises(AssertionError):schema_features(np.zeros((3,26)),ch)

    def test_BH_BY_missing_and_known_values(self):
        p=np.array([.01,.04,.03,.002,np.nan])
        np.testing.assert_allclose(fdr(p)[:4],[.02,.04,.04,.008])
        self.assertTrue(np.isnan(fdr(p)[-1]))
        self.assertTrue(np.all(fdr(p,'by')[:4]>=fdr(p)[:4]))

    def test_small_n_exact_signs_not_9999_independent_people(self):
        pv,n,kind=signflip(np.ones(5))
        self.assertEqual(n,32);self.assertEqual(kind,'exact')
        self.assertAlmostEqual(pv[0],2/32)

    def test_bootstrap_resamples_people_and_is_reproducible(self):
        a=np.column_stack([np.arange(22),2*np.arange(22)])
        x=bootstrap_means(a,101)
        np.testing.assert_array_equal(x,bootstrap_means(a,101))
        np.testing.assert_allclose(x[:,1],2*x[:,0])

    def test_FFT_circular_null_matches_direct_roll(self):
        rng=np.random.default_rng(2)
        y=rng.normal(size=(201,3));p=rng.normal(size=(201,3))
        result=cyclic_null(p,y,np.arange(201))
        gap=int(np.ceil(63/TR));shifts=range(gap,201-gap+1,2)
        expected=[np.mean([metric(p[:,j],np.roll(y[:,j],k))['r'] for j in range(3)]) for k in shifts]
        np.testing.assert_allclose(result['null_values'],expected,atol=1e-12)
        self.assertAlmostEqual(result['r'],np.mean([metric(p[:,j],y[:,j])['r'] for j in range(3)]))

    def test_gaps_block_null_instead_of_joining_segments(self):
        rng=np.random.default_rng(3);a=rng.normal(size=(201,2));frames=np.arange(201);frames[100:]+=1
        self.assertIsNone(cyclic_null(a,a,frames))

    def test_identity_and_actual_split(self):
        self.assertEqual(person('sub07-scan01'),'sub07')
        with self.assertRaises(ValueError):person('sub07-scan01_extra')
        result=folds(Path(__file__).resolve().parents[1]/'scan_split_cv5.xlsx')
        self.assertEqual(len(result),5)


if __name__=='__main__':unittest.main(verbosity=2)
