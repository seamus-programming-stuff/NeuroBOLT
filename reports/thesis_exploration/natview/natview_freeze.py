#!/usr/bin/env python3
"""Lock pilot-informed ingestion policy before any reserved EEG/BOLD bodies open."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from natview_data import COMMON,DERIV,OUT,ROOT,ATLAS,ATLAS_LABELS
from natview_stage import digest,save_json


def main():
    assert os.environ.get('SLURM_JOB_ID')
    assert not (OUT/'freeze.json').exists(),'Never silently overwrite a frozen protocol'
    qc=json.loads((OUT/'sub-01_qc.json').read_text())
    cache=json.loads((OUT/'VU_per_scan_cache_audit.json').read_text())
    training=json.loads((OUT/'model_training.json').read_text())
    finalized=json.loads((OUT/'model_finalization.json').read_text())
    geometry=json.loads((OUT/'bridge_geometry.json').read_text())
    assert qc['clock_resolved'] and qc['inclusion_pass'] and cache['passed']
    assert training['model_sha256']==digest(DERIV/'vu_common23_frozen.npz')
    assert finalized['final_model_sha256']==digest(DERIV/'vu_common23_prime_geometry_frozen.npz')
    assert finalized['coefficients_and_scalers_bitwise_unchanged']
    subjects=['sub-04','sub-05','sub-06','sub-08','sub-10','sub-11','sub-12','sub-13']
    for sub in subjects:
        assert not list((ROOT/f'preproc_data/{sub}/ses-01').rglob('*.set')),'Reserved EEG opened/staged before freeze'
        assert not list((ROOT/f'preproc_data/{sub}/ses-01').rglob('*.nii.gz')),'Reserved BOLD opened/staged before freeze'
    tests=subprocess.run([sys.executable,'scripts/natview_tests.py'],capture_output=True,text=True)
    (OUT/'frozen_tests.txt').write_text(tests.stdout+tests.stderr);tests.check_returncode()
    protocol={'version':1,'study':'NATVIEW new-site bounded external feasibility panel; implementation, not clinical validation',
       'development_person':'sub-01_ses-01','reserved_people':subjects,'session':'ses-01','task':'rest',
       'selection':'prespecified evidence/NATVIEW_PROPOSED_8person_repeat_extension.json, modality/visit availability only; all8 retained in denominator',
       'feature_channels':geometry['feature_channels_literal_VU'],'VU_literal_channels':'case differences retained in source; final two VU positions literally TP9-prime and TP10-prime, always interpolated at source directions',
       'bridge':{'n_features':23*44*12,'base':'drop VU F4/FT9/FT10 feature positions; retain existing VU reference',
                 'additional_missing_policy':'up to3 of21 exact nonprime sites may be interpolated from >=40 measured scalp donors; two prime sites always interpolated',
                 'geometry':'MNE accurate spherical spline using source NATVIEW donor and VU target direction vectors, normalized to95mm sphere, fixed origin0; explicit EEGLAB [X,Y,Z] to head [-Y,X,Z]; no outcome fitted geometry',
                 'geometry_sha256':digest(OUT/'bridge_geometry.json'),
                 'missing_metadata':json.loads((OUT/'reserved_montage_metadata_audit.json').read_text()),
                 'direct_measured_vs_interpolated':'report for each subject; do not call all23 commonly measured channels',
                 'reference':'NATVIEW average over released retained scalp montage; VU SET ref=common; these remain a domain shift'},
       'VU_model':{'training_only':'all29 existing VU scans; no ds006040 or NATVIEW training',
                   'selector':'per-target alpha retained from existing all26 VU cv_A geometric median across5 folds; NOT newly optimized for common23',
                   'training_standardization':'VU-only feature mean and sd+1e-8; no NATVIEW target-stat adaptation or calibration',
                   'model_sha256':finalized['final_model_sha256'],'initial_coefficient_fit_model_sha256':training['model_sha256'],
                   'coefficient_finalization':'bitwise unchanged coefficients/scalers; model channel metadata now literal prime labels',
                   'training_metadata_sha256':digest(OUT/'model_training.json'),
                   'per_scan_cache_audit_sha256':digest(OUT/'VU_per_scan_cache_audit.json')},
       'EEG_processing':{'units':'EEGLAB native uV; assert MNE volts*1e6 agrees within1e-4uV; no /100 neural scaling',
          'identity':'case-only canonicalization for NATVIEW, never replacement by another electrode',
          'sampling':'250to200Hz polyphase4/5 antialiasing separately within every physical segment',
          'filter':'MNE0.5Hz highpass zero phase separately within segment; 5s margins around 24s context',
          'features':'original baseline_ridge.band_power_features,44 one-Hz bins1..45Hz,12x2s lags oldestfirst, Welch nperseg200, log(power+1e-12)',
          'window':'4801samples including trigger for baseline mean; crop last sample to4800 as existing VU helper'},
       'clock':{'source':'raw ordered R128 are volume0..N-1; processed event->urevent links identify original volume',
          'requirements':'n_raw_R128=n_urevent_R128=n_BOLD; raw TR max deviation<=6ms; raw/urevent offset residual<=4.1ms',
          'mask':'clean_sample_mask true count=pnts; all surviving event anchors agree within1.01 samples; each interior mask gap has boundary at compressed location',
          'boundary_duration_discrepancy':'preserve source duration and exact mask gap length side by side; mask controls timing only after all anchor checks pass',
          'eye':'Time column already task-relative; do NOT add StartTime; >=90% volume pulses with unique nearest raw event within50ms',
          'BIOPAC':'sparse positive-code sample list; group samples within100ms; n_pulses=n_BOLD, relative first-pulse residual<=40ms',
          'volume_dropping':'zero as pinned CCS wrapper numDropping=0 and verified pilot raw/processed header counts',
          'no_prediction_alignment':'no offset, drift, lag or participant selection based on predicted/measured BOLD correlation'},
       'exclusions':{'window':'reject if 24s physical past plus5s filter margins on both sides crosses any mask gap or acquisition edge',
                     'amplitude':'any selected/interpolated channel peak-to-peak>500uV in4801samples',
                     'motion':'AFNI6 param Power FD50mm radius; FD>0.5mm and following frame excluded',
                     'channel':'exclude if >3 of21 nonprime sites absent or <40 measured donors with finite source coordinates',
                     'person':'minimum60 target frames (126s retained target duration), finite EEG/targets, all timing requirements; preserve failed-person denominator',
                     'strict_measured_comparison':'report measured nonprime coverage and interpolation counts; two VU prime sites are always interpolated, so no all23-measured claim; no choosing analysis by predictive scores'},
       'targets':{'atlas':str(ATLAS),'atlas_sha256':digest(ATLAS),'labels_sha256':digest(ATLAS_LABELS),
                  'regions':'NiftiMapsMasker DiFuMo64 maps resampled in world coordinates to released MNI3mm image; VU label identity/order checks',
                  'global':'mean of released MNI nonzero temporal support (sd>1e-8); native EPI mask not treated as MNI mask',
                  'released_processing':'noGSR/no temporal filter/sm0; CCS motion24 +WM/CSF; no additional fitted nuisance regression',
                  'postprocessing':'5th order0.15Hz Butterworth filtfilt; full-run demean/absolute95thpercentile normalization',
                  'differences':'NATVIEW CCS MNI152Lin vs existing VU derivative, distinct global-mask/reference/cleaning; common labels do not establish identical preprocessing'},
       'endpoints':{'primary':'unshifted temporal r globally and arithmetic mean over64 regions, per person then equally over people',
                    'amplitude':'normalized-target predictiveR2 and std(prediction)/std(target); no test calibration',
                    'residual':'regional and predicted global residualization using one VU-trained coefficient per region; no measured global model input',
                    'lag':'diagnostic -5..5 original volume indices, positive prediction later, minimum20 pairs; never changes primary alignment',
                    'CI':'2000 within-person stationary block bootstrap, expected10TR/21s block, restart at gaps;10000 between-person resamples, seed20261021'},
       'physiology':{'role':'independent timing/coverage QC only in this bounded test; pupil area not calibrated, respiration inV, no clinical arousal or sleep diagnosis',
                     'pilot_eye':'285pulses map volumes1..285; missing0/286/287;76.4% interpolated; Time is quantized, so no pupil-BOLD association claim'},
       'causal_context':'features have declared physical past context; source artifact/ICA correction, zero-phase filtering, interpolation and whole-run targets are retrospective',
       'license':'NKI NATVIEW data/code CC BY4.0; preserve source attribution and SHA256 receipts; no redistribution of raw arrays',
       'input_handoff_hashes':json.loads((OUT/'input_handoff_hashes.json').read_text()),
       'frozen_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'slurm_job_id':os.environ['SLURM_JOB_ID']}
    save_json(OUT/'protocol.json',protocol)
    deps=[Path('scripts/baseline_ridge.py'),Path('scripts/ext_transfer.py'),Path('scripts/interp_cv.py'),
          Path('scripts/eval_inter_per_scan.py'),Path('dataset_maker/preproc.py'),Path('dataset_maker/get_datasets.py')]
    hashes={str(p):digest(p) for p in sorted(Path('scripts').glob('natview_*.py'))+deps}
    freeze={'protocol_sha256':digest(OUT/'protocol.json'),'model_sha256':finalized['final_model_sha256'],
            'bridge_geometry_sha256':digest(OUT/'bridge_geometry.json'),
            'code_hashes':hashes,'pilot_QC_sha256':digest(OUT/'sub-01_qc.json'),'asset_manifest_sha256':digest(OUT/'asset_manifest.json'),
            'frozen_utc':protocol['frozen_utc'],'reserved_outcomes_opened':False,'slurm_job_id':os.environ['SLURM_JOB_ID']}
    save_json(OUT/'freeze.json',freeze)
    print('FROZEN',json.dumps(freeze,indent=2),flush=True)


if __name__=='__main__':main()
