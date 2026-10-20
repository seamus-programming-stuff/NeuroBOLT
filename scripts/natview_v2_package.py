#!/usr/bin/env python3
"""Secondary-v2 compact figures, strict-vs-amended summary, scheduler provenance."""
import argparse
import csv
import json
import os
import shutil
import subprocess
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from natview_stage import digest,save_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--jobs',required=True);a=p.parse_args();assert os.environ.get('SLURM_JOB_ID')
    base=Path('reports/thesis_exploration/natview');out=base/'v2'
    v1=json.loads((base/'v1/machine_summary.json').read_text());v2=json.loads((out/'machine_summary.json').read_text())
    lock=json.loads((out/'freeze.json').read_text())
    for path,h in {**lock['v1_code_hashes'],**lock['code_hashes']}.items():
        assert digest(path)==h,'Frozen source changed '+path
        cp=out/'source'/path;cp.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,cp)
    proto=json.loads((out/'protocol.json').read_text());people=proto['reserved_people'];df=pd.read_csv(out/'per_person_metrics.csv')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight'})
    fig,axes=plt.subplots(1,3,figsize=(13,4.9),sharey=True)
    for ax,target,title in zip(axes,['global','regional64','VU_global_adjusted_residual64'],['Global signal','Mean of64 regions','VU-global-adjusted regional residual']):
        dat=df[df.target==target].set_index('subject')
        for j,sub in enumerate(people):
            if sub not in dat.index:
                ax.text(-.95,j,'excluded: <60 frames',color='#777',va='center',fontsize=8);continue
            row=dat.loc[sub];ax.plot([row.r_CI_low,row.r_CI_high],[j,j],color='#709bb6',lw=2);ax.plot(row.r,j,'o',color='#165b91',ms=5)
        ax.axvline(0,color='#777',ls=':',lw=1);ax.set(title=title,xlim=(-1,1),xlabel='Unshifted temporal r');ax.grid(axis='x',alpha=.2)
    axes[0].set(yticks=np.arange(8),yticklabels=people);axes[0].invert_yaxis()
    fig.suptitle(f'NATVIEW amended v2 secondary feasibility: {v2["n_evaluated_people"]}/8 eligible people',fontsize=12)
    fig.text(.5,-.02,'Exploratory amendment after v1 mask-contract failures; unchanged model, thresholds and physical24s history. Bars: within-person block-bootstrap95% intervals.',ha='center',fontsize=8)
    fig.tight_layout();fig.savefig(out/'secondary_transfer_r.png',dpi=180);fig.savefig(out/'secondary_transfer_r.svg');plt.close(fig)
    cov=[];fig,ax=plt.subplots(figsize=(12,5.2))
    for i,sub in enumerate(people):
        q=json.loads((out/f'{sub}_qc.json').read_text());times=np.array(q['raw_scanner_onsets_task_seconds']);fr=q['feature_frames'];b=q['channel_bridge']
        ax.plot(times,np.full(len(times),i),'|',color='#e1e4e9',ms=10)
        for s in q['certified_segments']:
            start=s['original_start']/250-q['original_to_task_offset_seconds'];width=(s['original_stop_exclusive']-s['original_start'])/250
            ax.broken_barh([(start,width)],(i-.2,.4),facecolors='#d0dfd4')
        ax.plot(times[fr],np.full(len(fr),i),'|',color='#165b91' if q['inclusion_pass'] else '#a35f3c',ms=12)
        cov.append({'subject':sub,'included':q['inclusion_pass'],'frames':len(fr),'retained_target_seconds':len(fr)*2.1,
          'first_frame':int(fr[0]) if fr else None,'last_frame':int(fr[-1]) if fr else None,
          'first_target_task_seconds':float(times[fr[0]]) if fr else None,'last_target_task_seconds':float(times[fr[-1]]) if fr else None,
          'earliest_feature_history_task_seconds':float(times[fr[0]]-24) if fr else None,
          'target_acquisition_span_seconds':float(times[fr[-1]]-times[fr[0]]+2.1) if fr else 0,
          'measured_feature_sites':b['n_measured_features'],'interpolated_feature_sites':b['n_interpolated_features'],
          'interpolated_names':','.join(b['interpolated']),'eye_pulses':q['eye']['scanner_pulse_count'],
          'eye_max_clock_error_ms':q['eye']['max_abs_match_error_seconds']*1000,
          'biopac_max_clock_error_ms':q['biopac']['max_relative_clock_residual_seconds']*1000,
          'eye_interpolated_fraction':q['eye']['interpolated_fraction'],'mean_FD_mm':q['motion_QC']['mean_FD_mm'],
          'retained_frame_gaps':q['retained_frame_gaps'],**q['source_mask_diagnostic']})
    ax.set(yticks=np.arange(8),yticklabels=[f'{r["subject"]}  {r["frames"]} frames / {r["retained_target_seconds"]:.1f}s' for r in cov],
           xlabel='Physical task time (seconds)',title='V2: event-certified continuous spans and retained24s-history targets',xlim=(-12,625))
    ax.invert_yaxis();ax.grid(axis='x',alpha=.2);fig.tight_layout();fig.savefig(out/'secondary_physical_QC.png',dpi=180);fig.savefig(out/'secondary_physical_QC.svg');plt.close(fig)
    pd.DataFrame(cov).to_csv(out/'coverage_QC.csv',index=False)
    old=json.loads((base/'job_ledger.json').read_text())['jobs'];ids=list(dict.fromkeys(old+a.jobs.split(',')))
    r=subprocess.run(['sacct','-j',','.join(ids),'-o','JobID,JobName,State,ExitCode,Elapsed,MaxRSS,AllocCPUS,ReqMem,Start,End','-P'],capture_output=True,text=True,check=True)
    (out/'jobs_sacct.psv').write_text(r.stdout);save_json(out/'job_ledger.json',{'jobs':ids,'sacct':list(csv.DictReader(r.stdout.splitlines(),delimiter='|')),'package_job_id':os.environ['SLURM_JOB_ID']})
    study={'original_strict_v1':{'achieved_original_locked8_accuracy':False,'attempted':8,'eligible':v1['n_evaluated_people'],
              'meaning':'7 source-mask-contract failures; single eligible person is not8-person validation','protocol_sha256':v1['protocol_sha256'],
              'summary_path':str(base/'v1/machine_summary.json')},
           'amended_secondary_v2':{'achieved_amended_eligible_panel':True,'attempted':8,'clock_certified':v2['n_clock_resolved'],
              'eligible':v2['n_evaluated_people'],'excluded':v2['excluded_people'],'scope':v2['scope'],
              'pooled_metrics':v2['pooled_metrics'],'protocol_sha256':v2['protocol_sha256'],'summary_path':str(out/'machine_summary.json')},
           'model_sha256':v2['model_sha256'],'coefficients_scalers_bridge_unchanged':True,
           'min60_threshold_unchanged':True,'source_mask_repair':False,'BOLD_correlation_clock_selection':False,'clinical_claim':False,
           'staging':{'pilot_bytes':127034404,'reserved8_bytes':980089695,'full_corpus_download':False,'raw_arrays_pulled_locally':False},
           'practical_bounds':{'eyes_open_site_and_preprocessing_confound':True,'pupil_respiration_are_independent_measurements_not_clinical_truth':True,
                'amended_after_v1_exposure':True,'strict_vs_amended_must_be_reported':True},
           'source_hashes':{str(p):digest(p) for p in list(Path('scripts').glob('natview_*.py'))},
           'M3_paths':{'source_data':'/scratch/hz18/stay0060/NeuroBOLT/data/natview',
                       'v1_derivatives':'/scratch/hz18/stay0060/NeuroBOLT/checkpoints/ext/natview',
                       'v2_derivatives':'/scratch/hz18/stay0060/NeuroBOLT/checkpoints/ext/natview/v2'},
           'package_job_id':os.environ['SLURM_JOB_ID']}
    save_json(base/'study_summary.json',study)
    lines=['# NATVIEW execution results','',
        '**Strict original v1: not achieved as an8-person confirmation.** Seven recordings failed the cumulative source-mask contract; sub12 alone passed135 frames. The unchanged v1 record, sources and hashes are preserved in `v1/`.','',
        f'**Amended v2 secondary exploration: {v2["n_evaluated_people"]}/8 eligible after metadata-certified clock reconstruction.** All8 were attempted; sub05/sub10 remain below the unchanged60-frame gate. This is not the original untouched confirmation. Model coefficients, scalers, spatial bridge and all numeric QC thresholds stay unchanged.','',
        '| Endpoint | Person-mean r (95% person-bootstrap CI) | Normalized-target predictive R2 | Amplitude ratio |','|---|---:|---:|---:|']
    for m in v2['pooled_metrics']:
        ci=m['person_bootstrap_r_95CI'];lines.append(f'| {m["target"]} | {m["person_mean_r"]:.4f} [{ci[0]:.4f}, {ci[1]:.4f}] | {m["person_mean_normalized_target_predictive_R2"]:.4f} | {m["person_mean_amplitude_ratio"]:.4f} |')
    lines+=['','Per-person CIs, amplitude, lag profiles and all64 regional values are in `v2/per_person_metrics.csv` and `v2/regional_metrics.csv`. Lag is descriptive and never repairs clock alignment. `v2/coverage_QC.csv` retains all8 denominators, source mask counts, direct/interpolated channel counts, physical history coverage, motion and independent-clock evidence.','',
      'The v2 adapter requires monotonic exact integer original-minus-processed event offsets, anchors bracketing the whole history and filter margins, and a split at every source boundary. It never extrapolates or bridges a gap. The source mask is preserved as provenance. Some masks are consistent with an internal cleaning-stage mask; exact ASR substep identity is not established.','',
      'There are21 directly named nonprime sites plus2 always-interpolated VU TP9-prime/TP10-prime targets. Additional missing2–3 sites are interpolated in3 prespecified people using the fixed source-coordinate bridge. Native references remain different. Whole-run artifact correction/filtering/normalization are retrospective.','',
      'NATVIEW is instructed eyes-open rest at a new site; site, eye state and target preprocessing differences remain confounded. Pupil/respiration support independent timing/coverage QC only; missing/interpolated pupil is not sleep, and no clinical arousal claim is supported.','',
      'The observed coverage loss under fixed24s history motivates later tests of estimators that handle irregular/missing observations and explicitly abstain when context is insufficient. Those are future experiments, not results of an additional model arm here.','',
      'Reproduce from the repository on M3 using `scripts/natview_m3.sbatch`; phase order is stage pilot, inspect/train/cache audit/pilot/tests, v1 freeze, stage reserved8, v1 panel, preserve v1, metadata diagnostics, v2 audit, v2 freeze, v2 run. Exact locks and job records are supplied.','',
      f'Model SHA256: `{v2["model_sha256"]}`. V1 protocol: `{v1["protocol_sha256"]}`. V2 protocol: `{v2["protocol_sha256"]}`.','',
      'Data attribution: Nathan Kline Institute NATVIEW EEG-fMRI release, CC BY4.0. Source URLs, SHA256, ETags/response headers and licenses are retained in asset receipts and provenance. Original volumes/EEG remain on M3; there are no git commits or pushes.']
    (base/'README.md').write_text('\n'.join(lines)+'\n')
    save_json(out/'artifact_hashes.json',{'files':{str(p):digest(p) for p in out.glob('*') if p.is_file() and p.name!='artifact_hashes.json'},'packaging_source_sha256':digest(__file__)})
    print('V2 PACKAGED',v2['n_evaluated_people'],'eligible of8; original strict result preserved',flush=True)


if __name__=='__main__':main()
