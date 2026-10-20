#!/usr/bin/env python3
"""Preserve coefficient fit; make the two VU-prime electrode sites explicit."""
import json
import os
from pathlib import Path
import numpy as np
from natview_data import OUT,DERIV,COMMON
from natview_stage import digest,save_json


def main():
    assert os.environ.get('SLURM_JOB_ID')
    vu=json.loads((OUT/'VU_reference_audit.json').read_text())
    coords={r['label'].upper():np.array([r[k] for k in ['X','Y','Z']]) for r in vu['channel_coordinates'] if all(k in r for k in ['X','Y','Z'])}
    literal=[c if c not in ['TP9','TP10'] else c+"'" for c in COMMON]
    target={}
    for c in literal:
        p=coords[c];p=p/np.linalg.norm(p)
        target[c]=(-p[1]*.095,p[0]*.095,p[2]*.095)
    geometry={'feature_channels_literal_VU':literal,'target_positions_head_m':{k:list(map(float,v)) for k,v in target.items()},
              'source':str(OUT/'VU_reference_audit.json'),'source_sha256':digest(OUT/'VU_reference_audit.json'),
              'coordinate_rule':'VU EEGLAB directions normalized to95mm sphere; [Xanterior,Yleft,Zup] -> head [-Y,X,Z]; origin0',
              'always_interpolate':["TP9'","TP10'"],
              'additional_missing_policy':'at most3 of the21 exactly named nonprime sites; >=40 measured scalp donors with finite source SET coordinates',
              'donor_geometry':'each NATVIEW measured SET [X,Y,Z] direction normalized to95mm, same fixed EEGLAB->head transform; no signal-based fit',
              'interpolation':'MNE accurate spherical spline, origin[0,0,0]; keep source voltage reference',
              'slurm_job_id':os.environ['SLURM_JOB_ID']}
    save_json(OUT/'bridge_geometry.json',geometry)
    initial=DERIV/'vu_common23_frozen.npz';final=DERIV/'vu_common23_prime_geometry_frozen.npz'
    z=np.load(initial);values={k:z[k] for k in z.files};values['channels']=np.array(literal)
    np.savez_compressed(final,**values)
    new=np.load(final)
    unchanged=all(np.array_equal(new[k],z[k]) for k in z.files if k!='channels')
    assert unchanged
    save_json(OUT/'model_finalization.json',{'initial_model_path':str(initial),'initial_model_sha256':digest(initial),
              'final_model_path':str(final),'final_model_sha256':digest(final),'coefficients_and_scalers_bitwise_unchanged':unchanged,
              'only_model_container_change':'channels field records literal VU TP9-prime/TP10-prime names; NATVIEW bridge geometry handles them explicitly',
              'bridge_geometry_sha256':digest(OUT/'bridge_geometry.json'),'slurm_job_id':os.environ['SLURM_JOB_ID']})
    print('FINAL MODEL',digest(final),'weights bitwise unchanged',unchanged,flush=True)


if __name__=='__main__':main()
