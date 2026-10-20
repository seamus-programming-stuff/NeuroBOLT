#!/usr/bin/env python3
"""Bounded NATVIEW download; run on M3 login, never on compute nodes."""
import argparse
import concurrent.futures
import hashlib
import json
import os
import time
import urllib.request
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def save_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', required=True)
    p.add_argument('--root', required=True)
    p.add_argument('--receipt', required=True)
    p.add_argument('--panel', choices=['pilot', 'reserved8'], required=True)
    p.add_argument('--metadata-only', action='store_true', help='Channel identities only; no reserved outcome bodies')
    a = p.parse_args()
    if os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('Download only on login node')
    manifest = json.loads(Path(a.manifest).read_text())
    rows = [r for r in manifest if r['panel'] == a.panel]
    if a.metadata_only:
        rows = [r for r in rows if '/preproc_data/' in r['key'] and r['key'].endswith('_channels.tsv')]
    assert sum(r['size'] for r in rows) < (150_000_000 if a.panel == 'pilot' else 1_200_000_000)
    root = Path(a.root)
    def get(row):
        key = row['key']
        rel = key.split('NATVIEW_EEGFMRI/', 1)[1]
        assert '..' not in Path(rel).parts
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        headers = {}
        if not path.exists():
            for attempt in range(4):
                try:
                    with urllib.request.urlopen('https://fcp-indi.s3.amazonaws.com/' + key, timeout=120) as req:
                        headers = dict(req.headers)
                        with open(str(path) + '.partial', 'wb') as f:
                            while True:
                                b = req.read(1 << 20)
                                if not b:
                                    break
                                f.write(b)
                    assert Path(str(path) + '.partial').stat().st_size == row['size']
                    os.rename(str(path) + '.partial', path)
                    break
                except Exception:
                    if attempt == 3:
                        raise
                    time.sleep(2)
        assert path.stat().st_size == row['size'], str(path)
        result = {**row, 'url': 'https://fcp-indi.s3.amazonaws.com/' + key,
                  'path': str(path), 'sha256': digest(path), 'response_headers': headers,
                  'license': 'CC BY 4.0', 'attribution': 'Nathan Kline Institute NATVIEW EEG-fMRI release',
                  'staged_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
        print('STAGED', rel, row['size'], flush=True)
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        receipts = list(pool.map(get, rows))
    save_json(a.receipt, {'manifest_sha256': digest(a.manifest), 'files': receipts,
                        'total_bytes': sum(r['size'] for r in rows)})


if __name__ == '__main__':
    main()
