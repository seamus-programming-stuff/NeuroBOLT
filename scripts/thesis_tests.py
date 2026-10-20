#!/usr/bin/env python3
"""Synthetic sanity tests for causal inputs, fitted transforms and metrics."""
import json
import unittest
from pathlib import Path

import numpy as np
from scipy.signal import butter,sosfilt
from thesis_data import causal_downsample,causal_hr,window_features
from thesis_study import affine_calibration,correlations,lag_scores,r2,ridge_select,shifted_pairs,standardize,targets


class ThesisTests(unittest.TestCase):
    def test_causal_filter_future_invariance(self):
        rng=np.random.default_rng(4)
        x=rng.normal(size=(2,5000*3));b=x.copy();b[:,10000:]+=1e5
        a=causal_downsample(x,5000);c=causal_downsample(b,5000)
        np.testing.assert_array_equal(a[:,:400],c[:,:400])

    def test_hr_future_invariance_and_heart_rate(self):
        fs=200;t=np.arange(fs*80)/fs
        # Narrow QRS-like biphasic pulses every second, no EEG-band powers.
        phase=t%1;x=np.exp(-((phase-.1)/.015)**2)-.4*np.exp(-((phase-.14)/.02)**2)
        a,qa=causal_hr(x);b=x.copy();b[fs*45:]+=np.random.default_rng(1).normal(0,10,len(b)-fs*45)
        c,_=causal_hr(b)
        np.testing.assert_array_equal(a[:fs*45],c[:fs*45])
        self.assertGreater(qa['valid_fraction'],.5)
        self.assertAlmostEqual(qa['median_hr'],60,delta=2)

    def test_window_excludes_endpoint_and_future(self):
        rng=np.random.default_rng(3);x=rng.normal(size=(26,200*40));hr=np.full(200*40,70.)
        a,p=window_features(x,hr,30);x[:,6000:]=1e10;hr[6000:]=140
        b,q=window_features(x,hr,30)
        np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(p,q)
        self.assertEqual(a.shape,(300,));self.assertEqual(p.shape,(24,))

    def test_training_only_transforms(self):
        tr=np.array([[1.,2],[3,4],[np.nan,6]])
        (a,v),fit=standardize(tr,np.array([[100.,np.nan]]))
        (b,w),fit2=standardize(tr,np.array([[-1e8,1e8]]))
        np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(fit['median'],[2,4])
        self.assertTrue(np.isfinite(v).all())

    def test_ridge_matches_closed_form(self):
        rng=np.random.default_rng(2);x=rng.normal(size=(80,8));y=rng.normal(size=(80,3));v=rng.normal(size=(20,8))
        p,_=ridge_select(x,y,v,np.zeros((20,3)),np.full(20,1/20),[10.])
        xc=x-x.mean(0);w=np.linalg.solve(xc.T@xc+10*np.eye(8),xc.T@(y-y.mean(0)))
        np.testing.assert_allclose(p(v),(v-x.mean(0))@w+y.mean(0),atol=1e-9)

    def test_correlation_is_not_amplitude_calibration(self):
        y=np.linspace(-2,2,100)[:,None];p=.1*y
        self.assertAlmostEqual(correlations(p,y)[0],1)
        self.assertLess(r2(p,y)[0],.2)
        a,b=affine_calibration(p,y,np.full(100,.01))
        self.assertAlmostEqual(r2(p*a+b,y)[0],1)
        self.assertTrue(np.isnan(correlations(np.zeros_like(y),y)).all())

    def test_lag_with_real_frame_gaps(self):
        t=np.arange(150);y=np.sin(t*.31)[:,None];p=np.sin((t-2)*.31)[:,None]
        keep=np.r_[np.arange(50),np.arange(60,150)]
        self.assertEqual(lag_scores(p[keep],y[keep],t[keep])[0],4)

    def test_null_uses_actual_frame_grid(self):
        frames=np.array([0,1,2,5,6,7,8,9])
        pairs=shifted_pairs(frames,3)
        for a,b in pairs:
            self.assertEqual((frames[b]-frames[a])%10,3)
        self.assertLess(len(pairs),len(frames))

    def test_residual_coefficients_apply_without_refitting(self):
        rng=np.random.default_rng(5);g=rng.normal(size=100);ph=rng.normal(size=(100,3))
        y=np.c_[np.tile(g[:,None],(1,64))*2+rng.normal(size=(100,64))*.1,g]
        tr,b,bp=targets(y,ph)
        self.assertLess(np.std(tr[:,65:129]),.15)
        _,b2,bp2=targets(y*10,ph,b,bp)
        np.testing.assert_array_equal(b,b2);np.testing.assert_array_equal(bp,bp2)

    def test_protocol_grouping_if_present(self):
        p=Path('reports/thesis_exploration/data/protocol.json')
        if not p.exists():return
        protocol=json.loads(p.read_text());seen=[]
        for f in protocol['folds']:
            train=set(f['training_order']);val=set(f['validation_people']);test=set(f['test_people'])
            self.assertFalse(train&val or train&test or val&test)
            self.assertGreaterEqual(len(train),12);seen.extend(test)
        self.assertEqual(len(seen),len(set(seen)))


if __name__=='__main__':unittest.main(verbosity=2)
