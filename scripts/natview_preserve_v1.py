#!/usr/bin/env python3
"""Copy the completed strict-v1 record and exact frozen sources, without deletion."""
import json
import os
import shutil
from pathlib import Path
from natview_stage import digest,save_json


def main():
    assert os.environ.get('SLURM_JOB_ID')
    root=Path('reports/thesis_exploration/natview');dest=root/'v1'
    assert not dest.exists(),'Never overwrite a v1 snapshot'
    freeze=json.loads((root/'freeze.json').read_text());dest.mkdir()
    rows=[]
    for p in root.iterdir():
        if p.is_file():
            shutil.copy2(p,dest/p.name);rows.append({'source':str(p),'copy':str(dest/p.name),'sha256':digest(p)})
    if (root/'provenance').exists():shutil.copytree(root/'provenance',dest/'provenance')
    for p,h in freeze['code_hashes'].items():
        assert digest(p)==h,'Frozen v1 source changed '+p
        cp=dest/'source'/p;cp.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,cp)
    save_json(dest/'snapshot_receipt.json',{'strict_v1_freeze_sha256':digest(root/'freeze.json'),
          'files':rows,'source_hashes':freeze['code_hashes'],'slurm_job_id':os.environ['SLURM_JOB_ID'],
          'meaning':'strict original8-person attempt preserved, including7 exclusions and1 evaluable person; not an8-person accuracy confirmation'})
    print('PRESERVED V1',len(rows),'files',flush=True)


if __name__=='__main__':main()
