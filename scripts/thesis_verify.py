#!/usr/bin/env python3
"""Post-run integrity checks on completed cells, paired exports and archives."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from thesis_data import digest,save_json
from thesis_study import conditions

p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out
pr=json.loads((out/'protocol.json').read_text());summary=json.loads((out/'summary.json').read_text())
assert digest(out/'protocol.json')==(out/'protocol.sha256').read_text().split()[0]
assert summary['complete'] and summary['completed_cells']=={'ridge':48,'mlp':48}
scores=pd.read_csv(out/'per_person_scores.csv')
assert not scores.duplicated(['subject','input','model','training_people','duration_seconds','train_state','eval_condition','target']).any()
assert len(scores)==10368
test=set(p for f in pr['folds'] for p in f['test_people']);assert len(test)==27
for f,n,sec,info,state in conditions(pr):
    for model in ['ridge','mlp']:
        name=f"{model}_f{f['fold']}_n{n}_s{sec}_{info}_{state}"
        meta=json.loads((out/'cells'/f'{name}.json').read_text())
        assert {r['subject'] for r in meta['training_rows']}==set(f['training_order'][:n])
        assert not set(f['test_people'])&{r['subject'] for r in meta['training_rows']+meta['validation_rows']}
        assert meta['protocol_sha256']==digest(out/'protocol.json')
        assert sum(r['retained_target_seconds'] for r in meta['training_rows'])==n*sec
        assert meta['source_sha256']==pr['source_sha256']['thesis_study.py']
        rows=pd.read_csv(out/'cells'/f'{name}.csv')
        assert set(rows.subject)==set(f['test_people'])
        assert len(rows)==len(f['test_people'])*2*6
        assert set(rows.eval_condition)=={'EC','EO'}
        assert np.isfinite(rows.predictive_R2).all()
        assert (rows.circular_shift_matched_fraction>0).all()
z=np.load(out/'features_causal.npz');archives=list((out/'predictions').glob('*.npz'))
assert len(archives)==42
for file in archives:
    ar=np.load(file)
    for k in ar.files:
        if k.startswith('frame_'):
            run=k[6:];np.testing.assert_array_equal(ar[k],z[k])
            assert ar['pred_'+run].shape==ar['true_'+run].shape==(len(z[k]),193)
            assert np.isfinite(ar['pred_'+run]).all()
            # The first 65 outputs are simply reordered cached full targets.
            gi=list(z['labels'].astype(str)).index('global signal clean')
            order=[gi]+[i for i in range(65) if i!=gi]
            np.testing.assert_allclose(ar['true_'+run][:,:65],z['y_'+run][:,order],rtol=1e-6,atol=1e-6)
report={'passed':True,'completed_cells':96,'score_rows':len(scores),'outer_test_people':27,
        'highest_resource_prediction_archives':len(archives),'all_arms_use_same_original_test_frames':True,
        'training_label_budgets_verified':True,'group_separation_verified':True,'source_and_protocol_hashes_verified':True}
save_json(out/'verification.json',report);print(json.dumps(report,indent=2))
