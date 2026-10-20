#!/usr/bin/env python3
"""Bounded pinned code and raw NIfTI header acquisition on M3 login."""
import json
import os
import struct
import urllib.request
import zlib
from pathlib import Path
from natview_stage import digest, save_json


def main():
    assert not os.environ.get('SLURM_JOB_ID')
    out=Path('reports/thesis_exploration/natview/provenance');out.mkdir(parents=True,exist_ok=True)
    commit='a7ac63d526e13817e1031e8a910cc58b46a18ae7'
    paths=['fmri/ccs_preproc_bids_docker.sh','fmri/README.md',
           'fmri/preprocessing/ccs_bids_01_funcpreproc.sh','fmri/preprocessing/ccs_bids_04_funcnuisance.sh',
           'fmri/preprocessing/ccs_bids_05_funcpreproc_vol.sh','LICENSE']
    rows=[]
    for path in paths:
        url=f'https://raw.githubusercontent.com/NathanKlineInstitute/NATVIEW_EEGFMRI/{commit}/{path}'
        try:
            body=urllib.request.urlopen(url,timeout=60).read(200000)
            dest=out/Path(path).name;dest.write_bytes(body)
            rows.append({'url':url,'path':str(dest),'bytes':len(body),'sha256':digest(dest)})
        except Exception as exc:
            rows.append({'url':url,'error':str(exc)})
    url='https://fcp-indi.s3.amazonaws.com/data/Projects/NATVIEW_EEGFMRI/raw_data/sub-01/ses-01/func/sub-01_ses-01_task-rest_bold.nii.gz'
    req=urllib.request.Request(url,headers={'Range':'bytes=0-65535'})
    with urllib.request.urlopen(req,timeout=90) as f:
        body=f.read(65536);headers=dict(f.headers)
    dest=out/'pilot_raw_bold_header_range.gz';dest.write_bytes(body)
    raw=zlib.decompressobj(16+zlib.MAX_WBITS).decompress(body)
    endian='<' if struct.unpack('<i',raw[:4])[0]==348 else '>'
    rows.append({'url':url,'path':str(dest),'bytes':len(body),'sha256':digest(dest),'headers':headers,
                 'dim':list(struct.unpack(endian+'8h',raw[40:56])),
                 'pixdim':list(struct.unpack(endian+'8f',raw[76:108]))})
    save_json(out/'sources.json',rows)
    print(json.dumps(rows,indent=2))


if __name__=='__main__':
    main()
