#!/usr/bin/env python3
"""Save environment, run synthetic checks, and freeze protocol before fitting."""
import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

import mne
import numpy
import scipy
import torch
from thesis_data import freeze,save_json

p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
save_json(a.out/'environment.json',{'python':sys.version,'platform':platform.platform(),
          'numpy':numpy.__version__,'scipy':scipy.__version__,'torch':torch.__version__,'mne':mne.__version__,
          'cuda_build':torch.version.cuda})
r=subprocess.run([sys.executable,'scripts/thesis_tests.py'],capture_output=True,text=True)
(a.out/'synthetic_tests.txt').write_text(r.stdout+r.stderr,encoding='utf-8')
print(r.stdout+r.stderr,flush=True)
r.check_returncode()
freeze(a.out)
pr=json.loads((a.out/'protocol.json').read_text())
assert all(not(set(f['test_people'])&(set(f['training_order'])|set(f['validation_people']))) for f in pr['folds'])
print('PREPARED: No model outcomes inspected; protocol fixed.',flush=True)
