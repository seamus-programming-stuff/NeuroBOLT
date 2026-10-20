#!/usr/bin/env python3
"""Amended metadata adapter tests; no recording or BOLD values used."""
import copy
import unittest
import numpy as np
from natview_v2 import certified_adapter


def fixture():
    n=288;raw=np.arange(n)*2.1;gap=(25000,25500);anchors=[]
    for q in np.arange(n)*525:
        if gap[0]<=q<gap[1]:continue
        p=q-(500 if q>=gap[1] else 0)
        anchors.append({'type':'R128','processed_sample_0based':float(p),'original_sample_0based':float(q),
                        'offset_samples':float(q-p)})
    d={'subject':'synthetic','pnts':151200-500,'mask_length':151200,'mask_true_samples':151200,
       'mask_false_intervals':[],'raw_R128':n,'urevents_R128':n,'nvol':n,'events_R128':len(anchors),
       'raw_urevent_origin_residual_seconds':0,'raw_urevent_offset_seconds':0,
       'eye_pulses':285,'eye_unique_matched_volumes':285,'eye_max_abs_raw_match_error_seconds':.016,
       'eye_unmatched_volumes':[0,286,287],'biopac_pulses':n,'biopac_relative_first_residual_seconds':.024,
       'respiration_time_span_seconds':[0,610],'anchors':anchors,
       'boundaries':[{'latency':1,'duration':None},{'latency':25000.5,'duration':500}]}
    return d,raw


class AmendmentTests(unittest.TestCase):
    def test_stale_mask_does_not_replace_event_clock(self):
        d,t=fixture();source=copy.deepcopy(d);qc=certified_adapter(d,t)
        self.assertGreater(qc['retained_target_frames'],60)
        self.assertEqual(d,source)
        self.assertEqual(qc['source_mask_diagnostic']['mask_true_minus_payload_samples'],500)

    def test_no_gap_or_boundary_is_bridged(self):
        d,t=fixture();d['boundaries'].append({'latency':50000.5,'duration':0})
        qc=certified_adapter(d,t)
        for w in qc['certified_physical_windows']:
            p=w['event_sample_1based']-1
            self.assertLessEqual(w['processed_start'],p-29*250)
            self.assertGreaterEqual(w['processed_stop_exclusive']-1,p+5*250)
            self.assertFalse(p-29*250<25000<p+5*250)
            self.assertFalse(p-29*250<50000<p+5*250)

    def test_offset_decrease_rejects_clock(self):
        d,t=fixture();d['anchors'][-1]['original_sample_0based']-=1000
        d['anchors'][-1]['offset_samples']-=1000
        with self.assertRaises(ValueError):certified_adapter(d,t)

    def test_original_independent_thresholds_are_not_relaxed(self):
        d,t=fixture();d['eye_max_abs_raw_match_error_seconds']=.051
        with self.assertRaises(ValueError):certified_adapter(d,t)
        d,t=fixture();d['biopac_relative_first_residual_seconds']=.041
        with self.assertRaises(ValueError):certified_adapter(d,t)


if __name__=='__main__':unittest.main(verbosity=2)
