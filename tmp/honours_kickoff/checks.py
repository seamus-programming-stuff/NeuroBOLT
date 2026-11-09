import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

root = Path.cwd()
private = root / 'tmp/honours_kickoff'
source = [json.loads(line) for line in (private / 'source_inspection.ndjson').read_text(encoding='utf-8').splitlines()]
edited = [json.loads(line) for line in (private / 'build/edited_inspection.ndjson').read_text(encoding='utf-8').splitlines()]
by_id = {row.get('id'): row for row in edited}
changes, missing, checked = [], [], 0
for row in source:
    if not row.get('position') or row['kind'] == 'image':
        continue
    match = by_id.get(row['id'])
    if match is None:
        missing.append(row['id'])
        continue
    checked += 1
    if max(abs(row['position'][key] - match['position'][key]) for key in row['position']) > 0.1:
        changes.append({'slide': row.get('slideIndex', -1) + 1, 'id': row['id'], 'source': row['position'], 'output': match['position']})

pdf_path = root / 'output/pdf/Monash_EEG_honours_kickoff_v2.pdf'
pptx_path = root / 'output/presentations/Monash_EEG_honours_kickoff_v2.pptx'
pdf = PdfReader(pdf_path)
text = '\n'.join(page.extract_text() for page in pdf.pages)
assert len(pdf.pages) == 12
assert not any(word in text for word in ['Lorem ipsum', 'Title here', 'DRI name'])
assert len(text) > 1000
assert not missing and not changes, (missing, changes)
reference = Path('C:/Users/Seamus/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-project-kickoff/assets/reference.pptx')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
receipt = json.loads((private / 'final_v2.validation.json').read_text(encoding='utf-8'))
assert sha(pptx_path) == receipt['finalSha256']
assert sha(reference) == 'b1b15cb0c23ad524f9832749ec31b775719bae2bdba897de9c9d8556ca00a44c'
qa = {
    'referenceSha256': sha(reference),
    'sourceUnchanged': True,
    'sourceFramesChecked': checked,
    'missingOriginalShapes': missing,
    'frameChanges': changes,
    'pdfPages': len(pdf.pages),
    'pdfSizePoints': [float(pdf.pages[0].mediabox.width), float(pdf.pages[0].mediabox.height)],
    'pdfTextExtractable': True,
    'pptxSha256': sha(pptx_path),
    'pptxUnchangedByPdfExport': True,
    'pdfSha256': sha(pdf_path),
    'pdfExporter': 'Microsoft PowerPoint, read-only document opened without a visible window',
    'templateFamilyGate': 'The unmodified reference fails duplicate_placeholder_identity even when checked against itself. Original frames and all slide renders checked separately.',
    'intentionalContentChange': 'Checkerboard picture placeholder replaced with editable method diagram inside its original frame.',
    'knownSourceGeometry': 'Slide 8 timeline extends beyond the canvas in the reference and output, preserving the original crop.',
    'scope': 'Planning only. No new model runs, raw downloads or external contacts.',
}
(root / 'reports/honours_kickoff/qa.json').write_text(json.dumps(qa, indent=2) + '\n', encoding='utf-8')
(root / 'reports/honours_kickoff/validation.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(qa, indent=2))
