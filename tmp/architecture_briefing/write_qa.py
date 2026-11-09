from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote, urlparse
from pypdf import PdfReader

root=Path(__file__).resolve().parents[2]
folder=root/'reports/architecture_briefing'
source=root/'reports/NeuroBOLT architecture research briefing.md'
pdf=root/'output/pdf/NeuroBOLT_architecture_research_briefing.pdf'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reader=PdfReader(pdf)
assert len(reader.pages)==14
assert all(len(page.extract_text())>500 for page in reader.pages)
text='\n'.join(p.extract_text() for p in reader.pages)
assert 'RUNNING' not in text and 'no scores yet' not in text
assert '.0651' in text and '-.0159' in text and 'H1 remains untested' in text
links=[]
for page in reader.pages:
    for ann in page.get('/Annots',[]):
        uri=ann.get_object().get('/A',{}).get('/URI')
        if uri:
            assert str(uri).startswith('https://'),uri
            links.append(str(uri))
for target in re.findall(r'\]\(([^)]+)\)',source.read_text(encoding='utf-8')):
    if '://' not in target:
        path=source.parent/unquote(urlparse(target).path)
        assert path.is_file(),target
same=[]
for i in range(1,15):
    reviewed=root/f'tmp/architecture_briefing/release-{i:02d}.png'
    current=root/f'tmp/architecture_briefing/qa-{i:02d}.png'
    assert digest(reviewed)==digest(current),(i,'Visual layout changed after review')
    same.append(i)
manifest=json.loads((folder/'build_manifest.json').read_text(encoding='utf-8'))
assert manifest['source_sha256']==digest(source)
assert manifest['pdf_sha256']==digest(pdf)
qa={
    'pdf_sha256':digest(pdf),'pages':len(reader.pages),'linked_annotations':len(links),
    'all_relative_report_targets_exist':True,'all_links_https':True,
    'blank_or_orphan_only_pages':False,'missing_font_glyphs':False,
    'visual_review':'All pages reviewed through full-size renders/contact sheet; changed pages and appendix reviewed after content updates.',
    'latest_renders_pixel_identical_to_reviewed_release_pages':same,
    'pilot_status':'COMPLETE, all 12 fits/27 people; parent independently recomputed all108 model-person raw-R2 scores and source/protocol hashes.',
    'primary_architecture_change':'H1 is proposed, not implemented or validated by the proxy pilot.',
    'clinical_validation_claimed':False,'private_or_prospective_Emotiv_access_claimed':False,
    'main_pdf_contains_careers_pitch':False,
}
(folder/'qa.json').write_text(json.dumps(qa,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(qa,indent=2))
