from pathlib import Path
import hashlib
import json
import csv
import numpy as np

root = Path(__file__).resolve().parents[2]
run = root / 'reports/architecture_briefing/pilot/20261026_ec_global_v1'
protocol = json.loads((run/'protocol.json').read_text(encoding='utf-8'))
expected = (run/'protocol.sha256').read_text().split()[0]
assert hashlib.sha256((run/'protocol.json').read_bytes()).hexdigest() == expected
for name, digest in protocol['source_sha256'].items():
    assert hashlib.sha256((root/'scripts'/name).read_bytes()).hexdigest() == digest, name
rows = list(csv.DictReader((run/'per_person_scores.csv').open(encoding='utf-8')))
summary = json.loads((run/'summary_verified.json').read_text(encoding='utf-8'))
with np.load(run/'predictions.npz', allow_pickle=False) as z:
    for name in protocol['models']:
        scores=[]
        panel=[r for r in rows if r['model']==name]
        assert len(panel)==27 and len({r['subject'] for r in panel})==27
        for row in panel:
            who=row['subject']
            p=z[name+'_'+who].astype(float)
            y=z['true_'+who].astype(float)
            score=1-((p-y)**2).sum()/((y-y.mean())**2).sum()
            assert abs(score-float(row['predictive_R2']))<1e-6
            assert len(y)==int(row['n_frames'])
            scores.append(score)
        assert abs(np.mean(scores)-summary['models'][name]['predictive_R2']['mean'])<1e-6
        assert sum(s<0 for s in scores)==summary['models'][name]['negative_R2_count']
print('PASS: frozen protocol and all five source hashes; 108 model-person predictions, mean raw R2 and negative-R2 counts independently recomputed.')
