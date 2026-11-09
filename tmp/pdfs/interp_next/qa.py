from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote, urlparse
from pypdf import PdfReader

root=Path(__file__).resolve().parents[3]
run=root/'reports/interpretability_next/20261102_v2'
manifest=json.loads((run/'build_manifest.json').read_text(encoding='utf-8'))
pdf=root/manifest['PDF']
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(pdf)==manifest['PDF_sha256']
assert digest(root/'scripts/build_interp_next.py')==manifest['renderer_sha256']
reader=PdfReader(pdf)
assert len(reader.pages)==10
all_text='\n'.join(p.extract_text() for p in reader.pages)
assert '0.094' in all_text and '0.044' in all_text and '0.0189' in all_text
assert 'blocked' in all_text.lower() and 'remains untested' in all_text.lower()
assert '\ufffd' not in all_text
for page in reader.pages:
    assert tuple(float(x) for x in page.mediabox[2:])==(960,540)
    assert len(page.extract_text())>200
notes=(run/'presentation.md').read_text(encoding='utf-8')
assert len(re.findall(r'^## Slide \d+\.',notes,re.M))==10
assert notes.count('**Speaker notes**')==10
assert '$$R^2_' in notes
for md in (run/'presentation.md',run/'README.md'):
    for target in re.findall(r'\]\(([^)]+)\)',md.read_text(encoding='utf-8')):
        if '://' not in target:
            assert (md.parent/unquote(urlparse(target).path)).exists(),(md,target)
figure_paths=list((run/'figures').glob('*.svg'))
assert len(figure_paths)==11
for path in figure_paths:
    assert path.with_suffix('.pdf').is_file() and path.with_suffix('.png').is_file()
result={'PDF_sha256':digest(pdf),'pages':10,'size_points':[960,540],
        'speaker_notes':10,'scientific_figures':11,'source_formats':['SVG','PDF','PNG'],
        'relative_document_links_exist':True,'no_replacement_glyphs':True,
        'visual_review':'All ten full-size slide renders reviewed. Layout changes re-rendered and checked; final captions checked on slide5.',
        'known_incomplete_methods':'CKA/IG blocked by complete-CV provenance gate; no neural passes or new fits.',
        'scientific_verification':'11223 raw-R2 rows and both primary person-level bootstrap/sign-flip contrasts independently reproduced; see verification.json.',
        'renderer_sha256':manifest['renderer_sha256'],'protocol_sha256':manifest['protocol_sha256']}
(run/'qa.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(result,indent=2))
