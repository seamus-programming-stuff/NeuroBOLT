#!/usr/bin/env python3
"""Closing provenance and tabular-consistency checks; no new model arm."""
import csv
import json
import os
import time
from pathlib import Path
from natview_stage import digest,save_json


def main():
    assert os.environ.get('SLURM_JOB_ID')
    base=Path('reports/thesis_exploration/natview');v1=base/'v1';v2=base/'v2'
    first=json.loads((base/'freeze.json').read_text());second=json.loads((v2/'freeze.json').read_text())
    snapshot=json.loads((v1/'snapshot_receipt.json').read_text());checks=[]
    def check(path,expected,meaning):
        actual=digest(path);assert actual==expected,str(path)+' changed'
        checks.append({'path':str(path),'sha256':actual,'meaning':meaning})
    check(base/'freeze.json',snapshot['strict_v1_freeze_sha256'],'strict v1 freeze unchanged')
    for path in [base/'protocol.json',v1/'protocol.json']:check(path,first['protocol_sha256'],'strict v1 protocol unchanged')
    check(v2/'protocol.json',second['protocol_sha256'],'v2 protocol unchanged')
    for p,h in first['code_hashes'].items():
        check(Path(p),h,'current original-v1 source unchanged');check(v1/'source'/p,h,'archived frozen-v1 source unchanged')
    for p,h in {**second['v1_code_hashes'],**second['code_hashes']}.items():
        check(Path(p),h,'current v2/helper source unchanged');check(v2/'source'/p,h,'archived frozen-v2/helper source unchanged')
    for p,h in second['metadata_hashes'].items():check(Path(p),h,'v2 metadata certificates unchanged since freeze')
    for r in snapshot['files']:check(Path(r['copy']),r['sha256'],'preserved strict-v1 artifact unchanged')
    models=Path('/scratch/hz18/stay0060/NeuroBOLT/checkpoints/ext/natview')
    assert first['model_sha256']==second['model_sha256']
    for p in [models/'vu_common23_prime_geometry_frozen.npz',models/'v2/vu_common23_prime_geometry_frozen.npz']:
        check(p,first['model_sha256'],'v1/current/v2 final model containers unchanged')
    initial=json.loads((base/'model_training.json').read_text())
    check(models/'vu_common23_frozen.npz',initial['model_sha256'],'initial coefficient-fit container preserved')
    for p in [base/'bridge_geometry.json',v1/'bridge_geometry.json',v2/'bridge_geometry.json']:
        check(p,first['bridge_geometry_sha256'],'original fixed spatial bridge unchanged')
    s1=json.loads((v1/'machine_summary.json').read_text());s2=json.loads((v2/'machine_summary.json').read_text())
    assert s1['n_evaluated_people']==1 and len(s1['excluded_people'])==7
    assert s2['n_clock_resolved']==8 and s2['n_evaluated_people']==6
    assert {r['subject'] for r in s2['excluded_people']}=={'sub-05','sub-10'}
    metrics=list(csv.DictReader((v2/'per_person_metrics.csv').open()))
    coverage=list(csv.DictReader((v2/'coverage_QC.csv').open()))
    region=list(csv.DictReader((v2/'regional_metrics.csv').open()))
    assert len(metrics)==18 and len(region)==6*129 and len(coverage)==8
    assert sum(int(r['frames']) for r in coverage if r['included']=='True')==740
    assert all(r['subject'] not in {'sub-05','sub-10'} for r in metrics)
    for m in s2['pooled_metrics']:
        rr=[r for r in metrics if r['target']==m['target']]
        for a,b in [('r','person_mean_r'),('normalized_target_predictive_R2','person_mean_normalized_target_predictive_R2'),('amplitude_ratio','person_mean_amplitude_ratio')]:
            assert abs(sum(float(r[a]) for r in rr)/len(rr)-m[b])<1e-12
    save_json(base/'verification.json',{'status':'PASS','slurm_job_id':os.environ['SLURM_JOB_ID'],
              'completed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'hash_checks':checks,
              'strict_original_8person_confirmation_achieved':False,'strict_eligible':1,'amended_secondary_eligible':6,
              'prespecified_denominator':8,'accepted_frames':740,'possible_raw_frames':2304,
              'accepted_frame_fraction':740/2304,'summary_means_match_all_per_person_tables':True,
              'per_person_metric_rows':len(metrics),'region_metric_rows':len(region),
              'no_post_freeze_model_or_scaler_change':True,'frozen_spatial_bridge_unchanged':True,
              'v1_artifacts_unchanged':True,'v2_exploratory_scope_required':True,
              'source_contract_failures_are_not_biological_or_dataset_unusability_ceiling':True,
              'source_sha256':digest(__file__)})
    print('VERIFIED',len(checks),'hashes; v1 1/8; secondary6/8;740/2304frames; means consistent',flush=True)


if __name__=='__main__':main()
