#!/usr/bin/env python3
"""Small poster-ready exports with person bootstrap CIs and paired differences."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from thesis_data import digest,save_json

KEY=['input','model','training_people','duration_seconds','train_state','eval_condition','target']
METRICS=['r_mean','predictive_R2','validation_calibrated_R2','amplitude_ratio','best_lag_seconds',
         'absolute_best_lag_seconds','negative_R2_fraction','undefined_r_fraction','training_mean_R2',
         'circular_shift_r_mean','circular_shift_matched_fraction','rmse']


def estimate(a):
    a=np.asarray(a,dtype=float);a=a[np.isfinite(a)]
    if not len(a):return {'mean':None,'ci95':[None,None],'n_valid_people':0}
    rng=np.random.default_rng(20261021)
    draws=a[rng.integers(0,len(a),size=(2000,len(a)))].mean(1)
    return {'mean':float(a.mean()),'ci95':np.quantile(draws,[.025,.975]).tolist(),'n_valid_people':len(a)}


def paired(a,b,keys,kind,description):
    merged=a.merge(b,on=['subject']+keys,suffixes=('_a','_b'),validate='one_to_one')
    rows=[]
    for key,g in merged.groupby(keys,dropna=False):
        if not isinstance(key,tuple):key=(key,)
        row=dict(zip(keys,key));row.update({'contrast':kind,'description':description,'n_people':len(g)})
        for m in ['r_mean','predictive_R2','validation_calibrated_R2']:
            e=estimate(g[m+'_a'].to_numpy()-g[m+'_b'].to_numpy())
            row[m+'_difference']=e['mean'];row[m+'_difference_ci95']=e['ci95'];row[m+'_n_valid_people']=e['n_valid_people']
        rows.append(row)
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out
    files=sorted((out/'cells').glob('*.csv'))
    df=pd.concat([pd.read_csv(f) for f in files],ignore_index=True)
    # Each run is a person-condition in this release. The grouping explicitly
    # supports additional visits without treating visits as independent people.
    person=df.groupby(['dataset','scope','subject','fold']+KEY,dropna=False)[METRICS+['n_frames']].mean().reset_index()
    person['evaluation_role']='outer held-out development people; never used for tuning'
    person.to_csv(out/'per_person_scores.csv',index=False)
    summaries=[]
    for key,g in person.groupby(KEY,dropna=False):
        row=dict(zip(KEY,key));row['n_people']=len(g);row['n_folds']=int(g.fold.nunique())
        for m in METRICS:
            e=estimate(g[m]);row[m]=e['mean'];row[m+'_ci95']=e['ci95']
            if m=='r_mean':row['n_valid_r_people']=e['n_valid_people']
        summaries.append(row)
    contrasts=[]
    ec=person[person.train_state=='EC']
    specs=[(ec[ec.training_people==12],ec[ec.training_people==4],'training_people','people_12_minus_4','12 minus 4 training people, fixed retained seconds'),
           (ec[ec.duration_seconds==240],ec[ec.duration_seconds==120],'duration_seconds','seconds_240_minus_120','240 minus 120 retained target-seconds per person'),
           (ec[ec.input=='combined'],ec[ec.input=='eeg'],'input','combined_minus_eeg','Combined ECG timing+availability and EEG minus EEG'),
           (ec[(ec.input=='phys')&(ec.training_people==12)&(ec.duration_seconds==240)],ec[ec.input=='availability'],'input','phys_minus_availability','RR+availability minus availability only'),
           (person[person.model=='mlp'],person[person.model=='ridge'],'model','mlp_minus_ridge','Joint equal-group standardized-output MLP minus independent-output tuned ridge'),
           (person[person.eval_condition=='EO'],person[person.eval_condition=='EC'],'eval_condition','EO_minus_EC','Same fitted model, paired heldout people, EO minus EC condition'),
           (person[person.train_state=='EC_EO'],ec[(ec.training_people==12)&(ec.duration_seconds==240)],'train_state','mixed_minus_EC_training','Equal 240 retained seconds/person: 120 EC+120 EO minus 240 EC')]
    for aa,bb,removed,kind,desc in specs:
        keys=[k for k in KEY if k!=removed]
        contrasts.extend(paired(aa,bb,keys,kind,desc))
    aa=person[person.target=='regional64'];bb=person[person.target=='global_template_regional64']
    contrasts.extend(paired(aa,bb,[k for k in KEY if k!='target'],'regional_minus_global_template','Full regional prediction minus training-fitted predicted-global template'))
    protocol=json.loads((out/'protocol.json').read_text())
    qc=json.loads((out/'feature_qc.json').read_text())
    fits=[json.loads(p.read_text()) for p in sorted((out/'cells').glob('*.json'))]
    nmodels={m:sum(f['model']==m for f in fits) for m in ['ridge','mlp']}
    training=[]
    for f in fits:
        if f['model']=='ridge':
            for row in f['training_rows']:
                training.append({**{k:f[k] for k in ['fold','input','training_people','duration_seconds','train_state']},**row})
    pd.DataFrame(training).to_csv(out/'training_frame_manifest.csv',index=False)
    meta={'schema_version':1,'study':protocol['study'],'dataset':'ds006040','scope':protocol['scope'],
          'evaluation_role':'outer held-out development evaluation; previously inspected release, not untouched final external validation',
          'selection_role':protocol['selection'],'calibration_role':protocol['calibration'],
          'units':'cached whole-run demeaned/95th-percentile-normalized ROI targets; R2 and amplitude are not absolute patient BOLD calibration',
          'causality':'new input construction uses past samples only; inherited artifact removal, target preprocessing and frame QC are retrospective',
          'protocol_sha256':digest(out/'protocol.json'),'source_sha256':protocol['source_sha256'],
          'n_people':len(qc['people_complete_pairs']),'n_runs':2*len(qc['people_complete_pairs']),
          'completed_cells':nmodels,'expected_cells_per_model':48,'complete':all(nmodels[m]==48 for m in nmodels),
          'new_results_only':True,'independent_arousal_labels':False,'arousal_prototype_run':False,
          'failed_extraction_runs':qc['failed'],
          'uncertainty':'2000 percentile bootstrap resamples of people, paired by person for differences; exploratory intervals, no multiplicity correction, one subset order and one neural seed',
          'interpretation':'bounded learning-resource and state-shift comparisons; no scaling law, equivalence, clinical utility, or end-to-end online claim',
          'neural_objective':protocol['mlp_objective'],'ridge_objective':protocol['ridge_objective'],
          'conditions':summaries,'paired_contrasts':contrasts,
          'profile':json.loads((out/'profile.json').read_text()) if (out/'profile.json').exists() else None,
          'fit_seconds_total':{m:sum(f['elapsed_seconds'] for f in fits if f['model']==m) for m in nmodels},
          'max_peak_ram_MB':max(f['peak_ram_MB'] for f in fits),
          'max_gpu_peak_allocated_MB':max([f['gpu_peak_allocated_MB'] for f in fits if f['gpu_peak_allocated_MB'] is not None] or [0]),
          'sensor_quality':{'median_hr_valid_fraction':float(np.median([r['hr']['valid_fraction'] for r in qc['runs']])),
                            'min_hr_valid_fraction':float(min(r['hr']['valid_fraction'] for r in qc['runs']))}}
    save_json(out/'summary.json',meta)
    print('EXPORTED',len(person),'person-condition rows;',len(summaries),'conditions;',len(contrasts),'paired contrasts;',nmodels,flush=True)
    show=[r for r in summaries if r['training_people']==12 and r['duration_seconds']==240 and r['train_state']=='EC' and r['target'] in ['global','regional64','global_residual64']]
    for r in show:print({k:r[k] for k in ['input','model','eval_condition','target','r_mean','r_mean_ci95','predictive_R2','validation_calibrated_R2']},flush=True)


if __name__=='__main__':main()
