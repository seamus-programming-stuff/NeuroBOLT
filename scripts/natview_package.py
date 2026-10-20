#!/usr/bin/env python3
"""Compact NATVIEW result figures and scheduler evidence; no model/preprocessing edits."""
import argparse
import csv
import json
import os
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from natview_data import OUT
from natview_stage import digest,save_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--jobs',required=True);a=p.parse_args()
    assert os.environ.get('SLURM_JOB_ID')
    summary=json.loads((OUT/'machine_summary.json').read_text());protocol=json.loads((OUT/'protocol.json').read_text())
    ids=a.jobs.split(',')
    audit=subprocess.run(['sacct','-j',','.join(ids),'-o','JobID,JobName,State,ExitCode,Elapsed,MaxRSS,AllocCPUS,ReqMem,Start,End','-P'],capture_output=True,text=True,check=True)
    (OUT/'jobs_sacct.psv').write_text(audit.stdout)
    rows=list(csv.DictReader(audit.stdout.splitlines(),delimiter='|'))
    save_json(OUT/'job_ledger.json',{'jobs':ids,'sacct':rows,
        'semantic_status_note':'61207555/61207590 completed operationally but their pilot checks failed and prompted the recorded mask probe;61207671 failed literal-channel assert before corrected explicit source-name/frame audit61207729. No reserved outcomes opened during these repairs.',
        'package_job_id':os.environ['SLURM_JOB_ID']})
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.bbox':'tight'})
    # Physical timeline: original task clocks, not compressed cleaned sample index.
    subjects=['sub-01']+protocol['reserved_people'];fig,ax=plt.subplots(figsize=(12,5.3))
    labels=[]
    for i,sub in enumerate(subjects):
        path=OUT/f'{sub}_qc.json';clock=OUT/f'{sub}_clock.json'
        if not path.exists() and not clock.exists():labels.append(sub+' (failed clock)');continue
        q=json.loads((path if path.exists() else clock).read_text());off=q['original_to_task_offset_seconds']
        times=np.array(q['raw_scanner_onsets_task_seconds']);fr=q.get('feature_frames',[])
        ax.plot(times,np.full(len(times),i),'|',color='#d8dce3',ms=10,zorder=1)
        for lo,hi in q['removed_intervals_recording_seconds']:
            ax.broken_barh([(lo-off,hi-lo)],(i-.3,.6),facecolors='#dc7773',alpha=.75)
        if fr:ax.plot(times[fr],np.full(len(fr),i),'|',color='#165b91',ms=11,zorder=3)
        labels.append(f'{sub}  {len(fr)} frames / {len(fr)*2.1:.1f} s')
    ax.set(yticks=np.arange(len(subjects)),yticklabels=labels,xlabel='Physical task time (seconds)',
           title='NATVIEW: source EEG excisions and retained physical-history windows',xlim=(-12,625))
    ax.invert_yaxis();ax.grid(axis='x',alpha=.2)
    ax.plot([],[],'|',color='#165b91',ms=10,label='QC-passing target frame (24 s continuous history + 5 s margins)')
    ax.plot([],[],'s',color='#dc7773',ms=7,label='Source removed EEG interval')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.12),ncol=2,frameon=False,fontsize=8)
    fig.tight_layout();fig.savefig(OUT/'physical_clock_QC.png',dpi=180);fig.savefig(OUT/'physical_clock_QC.svg');plt.close(fig)
    if (OUT/'per_person_metrics.csv').exists():
        df=pd.read_csv(OUT/'per_person_metrics.csv');fig,axes=plt.subplots(1,3,figsize=(13,4.7),sharey=True)
        targets=['global','regional64','VU_global_adjusted_residual64'];titles=['Global signal','Mean of 64 regions','VU-global-adjusted regional residual']
        for ax,target,title in zip(axes,targets,titles):
            dat=df[df.target==target].set_index('subject').reindex(protocol['reserved_people'])
            ypos=np.arange(8)
            for j,(sub,row) in enumerate(dat.iterrows()):
                if pd.isna(row.r):continue
                ax.plot([row.r_CI_low,row.r_CI_high],[j,j],color='#6a9dbd',lw=2)
                ax.plot(row.r,j,'o',color='#165b91',ms=5)
            ax.axvline(0,color='#777',ls=':',lw=1);ax.set(title=title,xlabel='Unshifted temporal r',xlim=(-1,1))
            ax.grid(axis='x',alpha=.2)
        axes[0].set(yticks=np.arange(8),yticklabels=protocol['reserved_people']);axes[0].invert_yaxis()
        fig.suptitle('NATVIEW frozen external feasibility panel (prespecified n=8)',fontsize=12)
        fig.text(.5,-.025,'Bars: within-person stationary block-bootstrap 95% intervals. Native references, source cleaning and interpolation remain domain shifts.',ha='center',fontsize=8)
        fig.tight_layout();fig.savefig(OUT/'locked_transfer_r.png',dpi=180);fig.savefig(OUT/'locked_transfer_r.svg');plt.close(fig)
    coverage=[]
    for sub in subjects:
        path=OUT/f'{sub}_qc.json'
        if not path.exists():
            coverage.append({'subject':sub,'included':False,'frames':0});continue
        q=json.loads(path.read_text());b=q['channel_bridge']
        coverage.append({'subject':sub,'included':q['inclusion_pass'],'frames':q['n_feature_frames'],
          'retained_target_seconds':q['retained_target_seconds_after_all_QC'],'raw_volumes':q['n_volumes'],
          'processed_R128':q['processed_R128'],'removed_EEG_seconds':q['removed_seconds'],
          'measured_feature_sites':b['n_measured_features'],'interpolated_feature_sites':b['n_interpolated_features'],
          'interpolated_names':','.join(b['interpolated']),'eye_pulses':q['eye']['scanner_pulse_count'],
          'eye_interpolated_fraction':q['eye']['interpolated_fraction'],
          'eye_max_clock_error_ms':1000*q['eye']['max_abs_match_error_seconds'],
          'biopac_pulses':q['biopac']['pulse_count'],'biopac_max_clock_error_ms':1000*q['biopac']['max_relative_clock_residual_seconds'],
          'mean_FD_mm':q['motion_QC']['mean_FD_mm'],'retained_frame_gaps':q['retained_frame_gaps']})
    pd.DataFrame(coverage).to_csv(OUT/'coverage_QC.csv',index=False)
    artifact_hashes={str(p):digest(p) for p in OUT.glob('*') if p.suffix in ['.json','.csv','.png','.svg'] and p.name not in ['artifact_hashes.json']}
    save_json(OUT/'artifact_hashes.json',{'packaging_source_sha256':digest(__file__),'files':artifact_hashes})
    print('PACKAGED',summary['branch'],summary['n_evaluated_people'],'people',flush=True)


if __name__=='__main__':main()
