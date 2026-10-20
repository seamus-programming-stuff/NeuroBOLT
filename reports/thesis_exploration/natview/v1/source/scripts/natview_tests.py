#!/usr/bin/env python3
"""Focused invariants: clocks, excised physical time, identities, units and atlas."""
import unittest
import numpy as np
from natview_data import (COMMON,identity_indices,to_microvolts,sparse_pulses,
                          runs_of_true,validate_sample_map,physical_window_segment,atlas_order,common23_bridge)


class ContractTests(unittest.TestCase):
    def test_channel_identity_and_order(self):
        names=[c.lower() for c in COMMON[::-1]]
        self.assertEqual([names[i].upper() for i in identity_indices(names)],COMMON)
        with self.assertRaises(ValueError):identity_indices([c for c in COMMON if c!='F3']+['F4'])
        with self.assertRaises(ValueError):identity_indices(COMMON+['fp1'])

    def test_units(self):
        np.testing.assert_allclose(to_microvolts(np.array([1e-6,-2e-6]),'V'),[1,-2])
        np.testing.assert_allclose(to_microvolts([1,-2],'uV'),[1,-2])
        with self.assertRaises(ValueError):to_microvolts([1],'unknown')

    def test_explicit_interpolation_preserves_constant_and_measured_channels(self):
        import mne
        names=[c for c in COMMON if c!='F3']+['AF3','AF4','AF7','AF8','AFZ','FC1','FC2','FC3','FC4','FC5','FC6','FCZ',
              'CP1','CP2','CP3','CP4','CP5','CP6','CPZ','PO3','PO4','PO7','PO8','PO9','PO10','P1','P2']
        pos={k.upper():v for k,v in mne.channels.make_standard_montage('standard_1020').get_positions()['ch_pos'].items()}
        coordinates=[{'labels':c,'X':pos[c][1],'Y':-pos[c][0],'Z':pos[c][2]} for c in names]
        literal=COMMON[:-2]+["TP9'","TP10'"]
        geometry={'feature_channels_literal_VU':literal,'always_interpolate':["TP9'","TP10'"],
                  'target_positions_head_m':{c:pos[c.rstrip("'")].tolist() for c in literal}}
        data=np.ones((len(names),20));result,info=common23_bridge(data,names,coordinates,geometry)
        self.assertEqual(info['interpolated'],['F3',"TP9'","TP10'"])
        self.assertEqual(info['n_measured_features'],20)
        np.testing.assert_allclose(result,1,atol=1e-5)
        with self.assertRaises(ValueError):common23_bridge(np.ones((19,20)),COMMON[4:],[],geometry)

    def test_merged_boundary_duration_is_preserved_with_exact_mask_anchors(self):
        mask=np.ones(40,dtype=bool);mask[10:14]=False
        e={'srate':250,'pnts':36,'etc':{'clean_sample_mask':mask},
           'urevent':[{'type':'R128','latency':26.75}],
           'event':[{'type':'boundary','latency':10.5,'duration':2},
                    {'type':'R128','latency':22.75,'urevent':1}]}
        validate_sample_map(e)
        self.assertEqual(e['event'][0]['duration'],2)

    def test_sparse_trigger_codes(self):
        np.testing.assert_allclose(sparse_pulses([0,.016,2.096,2.112,4.2],[5]*5),[0,2.096,4.2])

    def test_exact_urevent_gap_reconstruction(self):
        mask=np.ones(40,dtype=bool);mask[10:14]=False
        e={'srate':250,'pnts':36,'etc':{'clean_sample_mask':mask},
           'urevent':[{'type':'R128','latency':26.75}],
           'event':[{'type':'boundary','latency':10.5,'duration':4},
                    {'type':'R128','latency':22.75,'urevent':1}]}
        _,_,rows,_=validate_sample_map(e)
        self.assertEqual(rows[0]['volume'],0)
        self.assertAlmostEqual(rows[0]['mask_reconstruction_error_samples'],0)
        e['event'][1]['latency']=19.75
        with self.assertRaises(ValueError):validate_sample_map(e)

    def test_no_window_crosses_excised_time(self):
        mask=np.ones(100*250,dtype=bool);mask[20*250:25*250]=False
        segments=runs_of_true(mask)
        self.assertIsNone(physical_window_segment(segments,40))
        self.assertEqual(physical_window_segment(segments,60),(6250,25000))
        self.assertIsNone(physical_window_segment(segments,97))

    def test_atlas_identity(self):
        labels=[f'region{i}' for i in range(64)]
        self.assertEqual(atlas_order(labels,labels[::-1]+['global signal clean']),list(range(63,-1,-1))+[64])
        with self.assertRaises(ValueError):atlas_order(labels,labels[:-1]+['Schaefer','global signal clean'])


if __name__=='__main__':unittest.main(verbosity=2)
