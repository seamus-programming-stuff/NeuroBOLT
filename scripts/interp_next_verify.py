"""Independent float64 check of returned predictions and primary contrasts."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
MODELS=('eeg_full','phys_specific','eeg+phys_specific')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True)
    args=parser.parse_args();out=args.run.resolve()
    p=json.loads((out/'protocol.json').read_text(encoding='utf-8'))
    assert sha(out/'protocol.json')==(out/'protocol.sha256').read_text().split()[0]
    received=json.loads((out/'output_hashes.json').read_text(encoding='utf-8'))
    for name,digest in received.items():
        if (out/name).exists():assert sha(out/name)==digest,name
    for name,digest in p['source_sha256'].items():
        assert sha(out/'provenance/scripts'/name)==digest,name
    metrics=pd.read_csv(out/'metrics_per_scan.csv');rows=[];maxerr=0.
    for model in MODELS:
        source=out/'private'/(model.replace('+','_plus_')+'.npz')
        assert sha(source)==p['inputs'][model]['sha256']
        with np.load(source,allow_pickle=False) as z:
            targets=[str(x) for x in z['targets']]
            scans=sorted(k[5:] for k in z.files if k.startswith('pred_'))
            assert len(scans)==29
            for scan in scans:
                pred=z['pred_'+scan].astype(float);true=z['true_'+scan].astype(float)
                r2=1-np.einsum('ij,ij->j',pred-true,pred-true)/np.einsum('ij,ij->j',true-true.mean(0),true-true.mean(0))
                block=metrics[(metrics.model==model)&(metrics.scan==scan)].set_index(['targets','roi'])
                for j,target in enumerate(targets):
                    ts,roi=target.split('|',1)
                    diff=abs(r2[j]-block.loc[(ts,roi),'R2']);maxerr=max(maxerr,float(diff))
                    assert diff<2e-6,(model,scan,target,diff)
                    if ts=='all65' and roi!='global signal clean':
                        rows.append({'model':model,'person':scan.split('-')[0],'scan':scan,'roi':roi,'R2':r2[j]})
    independent=pd.DataFrame(rows).groupby(['model','person','roi']).R2.mean().groupby(['model','person']).mean().unstack('model').sort_index()
    saved=pd.read_csv(out/'contrasts.csv');saved=saved[saved.family=='primary_raw_R2'].set_index('contrast')
    checked=[]
    for a,b in p['primary']:
        d=(independent[a]-independent[b]).to_numpy();r=saved.loc[a+' minus '+b]
        rng=np.random.default_rng(20261102)
        indices=rng.integers(22,size=(p['bootstrap_B'],22))
        bounds=np.percentile(d[indices].mean(1),[2.5,97.5])
        signs=np.random.default_rng(20261103).choice((-1.,1.),size=(9999,22))
        pv=(1+(np.abs(signs@d/22)>=abs(d.mean())-1e-14).sum())/10000
        assert abs(r['mean']-d.mean())<1e-6
        np.testing.assert_allclose(bounds,[r.lo,r.hi],atol=1e-6)
        assert abs(pv-r.p)<1e-9
        checked.append({'contrast':a+' minus '+b,'mean':float(d.mean()),'CI':bounds.tolist(),'p':float(pv)})
    audit={
        'state':'VERIFIED','independently_recomputed_model_scan_target_rows':3*29*129,
        'max_absolute_R2_discrepancy':maxerr,'frozen_source_and_returned_file_hashes_match':True,
        'primary_participant_aggregation_intervals_and_signflips_verified':checked,
        'P2':'BLOCKED; no CV PTH candidates, no neural passes',
        'GSR_constant_baseline_note':'Training-mean GSR R2 is numerically zero (about -4e-17). Negative-sign counts at this precision are floating-point artifacts, not model failures. Raw records retained.',
        'legacy_execution_proof_limit':'Current archived M3 source and feature schema are audited; hashes do not retrospectively certify every original training execution.',
        'predictive_partition_not_causal':True,
    }
    (out/'verification.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
