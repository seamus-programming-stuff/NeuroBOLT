#!/usr/bin/env python3
"""Build the thesis-exploration poster using example2.pdf's measured geometry.

Run with the bundled ReportLab runtime. The artifact-operation marker is a
workflow precondition, deliberately not repeated inside this reusable builder.
No input experiments, research notes or earlier posters are modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "reports/thesis_exploration/poster"
REFERENCE_ID = 'Examples.zip/Files/example2.pdf'
# Verified from the supplied PDF and the first measured-layout build manifest.
REFERENCE_SHA256 = '6cbcaa767705fab9f998e7bfbe85e27b66d7da3c3dcd356359c5c3fd43cd6e83'
W, H = 2383.937, 3370.394
BLUE, ORANGE = "#00A2FF", "#FF9300"
INK, MUTED, GRID = "#151515", "#4A5158", "#D9E0E6"
GEOMETRY = {
    "title": [56.69287, 56.693, 2270.55113, 264.323],
    "problem": [97.69085, 349.564, 562.3009, 412.1302],
    "architecture": [96.42254, 823.416, 563.5692, 811.9902],
    "aim": [727.6812, 349.141989, 1556.084, 554.643111],
    "hypothesis": [727.6812, 923.499997, 1556.084, 284.931503],
    "clinical_path": [725.0, 1242.0, 457.0, 335.0],
    "models": [1270.667, 1244.524, 1015.599, 388.3821],
    "divider": [56.69287, 1665.627, 2270.55113, 102.619],
    "methods": [96.42254, 1820.803, 920.1018, 461.395],
    "results": [1078.925, 1820.803, 1204.341, 420.5544],
    "work_packages": [1078.925, 2285.198, 1204.341, 420.5544],
    "clinical_gate": [1078.925, 2753.2483, 1204.341, 484.6679],
    "learning": [96.42254, 2440.0, 920.1018, 737.0],
    "natview_inset": [96.42254, 2905.0, 920.1018, 272.0],
    "author": [1191.9685, 3275.274],
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def source_path(value):
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference_provenance(path=None):
    """The private example is optional; geometry and its verified hash are saved."""
    path=Path(path) if path is not None else ASSETS/'reference/example2.pdf'
    if path.is_file():
        if sha(path)!=REFERENCE_SHA256:
            raise ValueError('Local reference differs from the measured example2 PDF')
        status='local bytes verified; layout uses recorded geometry'
    else:
        status='not loaded; recorded verified SHA256 and measured geometry'
    return dict(reference=REFERENCE_ID,reference_sha256=REFERENCE_SHA256,
                reference_file_status=status,reference_content_embedded=False)


def fonts():
    fontdir = Path("C:/Windows/Fonts")
    for name, file in (("Body", "arial.ttf"), ("Body-Bold", "arialbd.ttf"),
                       ("Body-Italic", "ariali.ttf"), ("Body-BoldItalic", "arialbi.ttf"),
                       ("Display", "ariblk.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(fontdir / file)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                                  italic="Body-Italic", boldItalic="Body-BoldItalic")


def native_adapter(summary_path, people_path, protocol_path):
    """Map native exports to the outcome-independent panels and audit means.

    This checks exported statistics, not scheduler completion or clinical validity.
    Review permissions belong to the coordinator and are never set here.
    """
    s=read_json(summary_path); protocol=read_json(protocol_path)
    selection=read_json(ASSETS/'panel_selection.json')
    declared=protocol['poster_primary_prespecified']
    fixed=dict(train_state='EC',eval_condition='EC',training_people=12,
               duration_seconds=240,target='regional64')
    if any(declared.get(k)!=v for k,v in fixed.items()):
        raise ValueError('Worker protocol differs from predeclared primary; annotate a feasibility amendment')
    if s['protocol_sha256'] != sha(protocol_path):
        raise ValueError('Native summary protocol hash mismatch')
    if s.get('complete') is not True:
        raise ValueError('Native summary is incomplete')
    with people_path.open(encoding='utf-8-sig',newline='') as f:
        people=list(csv.DictReader(f))
    def matches(r,filters):
        return all(str(r.get(k))==str(v) for k,v in filters.items())
    def point(filters,label):
        entries=[r for r in s['conditions'] if matches(r,filters)]
        if len(entries)!=1:raise ValueError(f'Expected one native cell: {filters}')
        cell=entries[0]
        pp=[r for r in people if matches(r,filters)]
        if len(pp)!=int(cell['n_people']) or len({r['subject'] for r in pp})!=len(pp):
            raise ValueError(f'Participant count/duplication mismatch: {filters}')
        rr=[float(r['r_mean']) for r in pp]
        finite=[v for v in rr if math.isfinite(v)]
        mean=sum(finite)/len(finite)
        if abs(mean-float(cell['r_mean']))>1e-10:
            raise ValueError(f'Native mean disagrees with person CSV: {filters}')
        if len(finite)!=int(cell['n_valid_r_people']):
            raise ValueError('Undefined-correlation denominator mismatch')
        if len({r['fold'] for r in pp})!=3:
            raise ValueError('Selected native cell does not span all three outer folds')
        low,high=cell['r_mean_ci95']
        return dict(model=f"{cell['model']}/{cell['input']}",label=label,
                    condition=f"{cell['train_state']}->{cell['eval_condition']}",
                    target=cell['target'],metric='temporal_r',mean=mean,ci_low=low,ci_high=high,
                    n_people=len(pp),train_people=cell['training_people'],
                    target_seconds_per_person=cell['duration_seconds'],native_selector=filters,
                    predictive_R2=cell['predictive_R2'],negative_R2_fraction=cell['negative_R2_fraction'],
                    undefined_r_fraction=cell['undefined_r_fraction'],n_valid_r_people=len(finite))
    arms=[('ridge','eeg','Ridge EEG'),('ridge','phys','Ridge ECG timing'),
          ('ridge','combined','Ridge EEG+ECG'),('mlp','eeg','MLP EEG')]
    primary=[point({**fixed,'model':m,'input':i},label) for m,i,label in arms]
    learning=[]
    for duration in (120,240):
        for n in (4,12):
            learning.append(point({**fixed,'model':'ridge','input':'eeg',
                                   'training_people':n,'duration_seconds':duration},'Ridge EEG'))
    contrast_filters={**fixed,'model':'ridge','input':'eeg'}
    contrasts={}
    for name in ('people_12_minus_4','seconds_240_minus_120','regional_minus_global_template'):
        # Contrasts omit the changed factor in their own native schema.
        ff={k:v for k,v in contrast_filters.items() if
            not (name=='people_12_minus_4' and k=='training_people') and
            not (name=='seconds_240_minus_120' and k=='duration_seconds') and
            not (name=='regional_minus_global_template' and k=='target')}
        cc=[r for r in s['paired_contrasts'] if r['contrast']==name and matches(r,ff)]
        if len(cc)!=1:raise ValueError(f'Nonunique/missing paired contrast: {name}')
        contrasts[name]=cc[0]
    sources=[summary_path,people_path,protocol_path]
    # Worker exports can have a different row order; match exact predeclared cells.
    for name,points in (('poster_scores.csv',primary),('poster_learning.csv',learning)):
        pp=summary_path.parent/name
        with pp.open(encoding='utf-8-sig',newline='') as f:
            exported=list(csv.DictReader(f))
        if len(exported)!=4:raise ValueError(f'Unexpected worker panel row count: {pp}')
        for point_row in points:
            ee=[r for r in exported if f"{r['estimator']}/{r['input']}"==point_row['model'] and
                int(r['train_people'])==point_row['train_people'] and
                int(r['target_seconds_per_person'])==point_row['target_seconds_per_person'] and
                r['target']=='regional64' and r['condition']=='EC train / EC test']
            if len(ee)!=1:raise ValueError(f'Exported panel disagrees with locked selection: {point_row}')
            for key in ('mean','ci_low','ci_high','predictive_R2','n_people'):
                if abs(float(ee[0][key])-float(point_row[key]))>1e-10:
                    raise ValueError(f'Exported {key} disagrees with native/person-level audit')
        sources.append(pp)
    for name in ('verification.json','package_verification.json'):
        pp=summary_path.parent/name
        if read_json(pp).get('passed') is not True:raise ValueError(f'Worker verification failed: {pp}')
        sources.append(pp)
    job_path=summary_path.parent/'job_evidence.json'
    jobs=[r for r in read_json(job_path)['jobs'] if str(r['JobID']).isdigit()]
    if len(jobs)!=9 or any(r['State']!='COMPLETED' or r['ExitCode']!='0:0' for r in jobs):
        raise ValueError('Expected nine completed, successful ds006040 root jobs')
    sources.append(job_path)
    return dict(status='native exports checked; coordinator review is separate',
                selection_id=selection['selection_id'],protocol_sha256=s['protocol_sha256'],
                n_people=s['n_people'],n_runs=s['n_runs'],primary_rows=primary,learning_rows=learning,
                contrasts=contrasts,uncertainty=s['uncertainty'],
                completed_jobs=[dict(job_id=r['JobID'],state=r['State'],exit_code=r['ExitCode']) for r in jobs],
                source_files=[dict(path=str(p),sha256=sha(p)) for p in sources])


def natview_adapter(summary_path,people_path):
    """Check the amended panel, preserving strict-v1 QC and all-eight coverage."""
    s=read_json(summary_path);root=summary_path.parent
    strict_path=root.parent/'machine_summary.json';strict=read_json(strict_path)
    if sha(strict_path)!=s['original_v1_summary_sha256']:
        raise ValueError('Preserved strict-v1 summary hash mismatch')
    if strict['n_prespecified_people']!=8 or strict['n_evaluated_people']!=1:
        raise ValueError('Strict v1 acceptance is not the documented 1/8 QC result')
    if s['original_strict_8person_confirmation_achieved'] is not False or not s['pilot_used_for_ingestion_only']:
        raise ValueError('Amended NATVIEW must not be labelled original confirmation or include pilot')
    if s['model_coefficients_scalers_unchanged'] is not True or s['model_sha256']!=strict['model_sha256']:
        raise ValueError('NATVIEW frozen model changed across the amendment')
    protocol_path=root/'protocol.json';freeze_path=root/'freeze.json'
    if sha(protocol_path)!=s['protocol_sha256'] or sha(freeze_path)!=s['freeze_sha256']:
        raise ValueError('NATVIEW protocol/freeze hash mismatch')
    with people_path.open(encoding='utf-8-sig',newline='') as f:
        rr=[r for r in csv.DictReader(f) if r['target']=='regional64']
    cell=next(r for r in s['pooled_metrics'] if r['target']=='regional64')
    if len(rr)!=6 or len({r['subject'] for r in rr})!=6 or cell['n_people']!=6:
        raise ValueError('NATVIEW expected six distinct QC-passing people')
    for key,nativekey in (('r','person_mean_r'),('normalized_target_predictive_R2','person_mean_normalized_target_predictive_R2')):
        mean=math.fsum(float(r[key]) for r in rr)/len(rr)
        if abs(mean-cell[nativekey])>1e-12:raise ValueError(f'NATVIEW person CSV mean mismatch: {key}')
    qcs={r['subject']:read_json(root/(r['subject']+'_qc.json')) for r in s['per_person_QC']}
    if len(qcs)!=8 or not all(q['clock_resolved'] for q in qcs.values()):
        raise ValueError('NATVIEW all-eight clock denominator mismatch')
    accepted={r['subject'] for r in rr};failed={r['subject'] for r in s['excluded_people']}
    if len(failed)!=2 or accepted & failed or accepted|failed != set(qcs):
        raise ValueError('NATVIEW accepted/excluded partition fails all-eight accounting')
    for r in rr:
        q=qcs[r['subject']]
        if int(r['n_frames'])!=q['n_feature_frames'] or not q['inclusion_pass']:
            raise ValueError('NATVIEW scored frame/QC mismatch')
    scored=sum(int(r['n_frames']) for r in rr);total=sum(q['n_volumes'] for q in qcs.values())
    if scored!=740 or total!=2304:raise ValueError('Reviewed NATVIEW all-eight coverage changed')
    with (root/'jobs_sacct_final.psv').open(encoding='utf-8-sig',newline='') as f:
        jobs=list(csv.DictReader(f,delimiter='|'))
    for jid in ('61208118','61208120'):
        jj=[r for r in jobs if r['JobID']==jid]
        if len(jj)!=1 or jj[0]['State']!='COMPLETED' or jj[0]['ExitCode']!='0:0':
            raise ValueError('NATVIEW scoring/reporting jobs not successfully complete')
    low,high=cell['person_bootstrap_r_95CI'];mean=cell['person_mean_r']
    r2=cell['person_mean_normalized_target_predictive_R2']
    panel=dict(outcome='prediction',n_people=6,n_reserved_people=8,n_accepted_people=6,n_failed_people=2,
               v1_accepted_people=1,pilot_excluded=True,amendment_role='secondary exploratory after QC',
               scope=s['scope'],mean=mean,ci_low=low,ci_high=high,predictive_R2=r2,
               predictive_R2_ci95=cell['person_bootstrap_R2_95CI'],scored_frames=scored,total_frames=total,
               metric_label=f'Regional r {mean:.3f} [{low:.4f}, {high:.3f}]',
               coverage_caption=f'R2 {r2:.3f}; {scored}/{total} frames ({100*scored/total:.1f}%).',
               montage_caption='Frozen VU model/thresholds; 23 target sites include interpolation.',
               protocol_sha256=s['protocol_sha256'],model_sha256=s['model_sha256'])
    sources=[summary_path,people_path,strict_path,protocol_path,freeze_path,root/'jobs_sacct_final.psv',root/'coverage_QC.csv']
    sources.extend(root/(pid+'_qc.json') for pid in qcs)
    return dict(panel=panel,source_files=[dict(path=str(p),sha256=sha(p)) for p in sources],
                accepted_ids=sorted(accepted),failed_ids=sorted(failed),
                frame_counts={r['subject']:int(r['n_frames']) for r in rr},status='native NATVIEW audit passed')


def inputs(path, final):
    data = read_json(path) if path.exists() else {}
    rows, curves, provenance = [], [], []
    if data:
        if data.get('native_summary'):
            audit=native_adapter(source_path(data['native_summary']),source_path(data['native_people_csv']),
                                 source_path(data['native_protocol']))
            provenance.extend(audit['source_files'])
            # Only an explicit coordinator review enables even draft numeric panels.
            if data.get('results_reviewed') is True:
                rows=audit['primary_rows'];curves=audit['learning_rows']
                if not data.get('completed_jobs'):data['completed_jobs']=audit['completed_jobs']
            data['native_audit']=audit
        if data.get('natview_reviewed') is True and data.get('native_natview_people_csv'):
            nv=natview_adapter(source_path(data['natview_summary']),source_path(data['native_natview_people_csv']))
            data['natview_panel']=nv['panel'];provenance.extend(nv['source_files'])
            data['natview_native_audit']=nv
        for key in ("scores_csv", "learning_csv"):
            if data.get(key):
                p = source_path(data[key])
                with p.open(encoding="utf-8-sig", newline="") as f:
                    values = list(csv.DictReader(f))
                if key == "scores_csv":
                    rows = values
                else:
                    curves = values
                provenance.append({"path": str(p), "sha256": sha(p)})
        if data.get("primary_view"):
            rows = [r for r in rows if all(str(r.get(k, "")) == str(v)
                                           for k, v in data["primary_view"].items())]
        for row in rows + curves:
            required = ("model", "condition", "target", "metric", "mean", "ci_low", "ci_high", "n_people")
            missing = [k for k in required if not row.get(k)]
            if missing:
                raise ValueError(f"Missing score columns/values: {missing}")
            for k in ("mean", "ci_low", "ci_high"):
                row[k] = float(row[k])
                if not math.isfinite(row[k]):
                    raise ValueError(f"Non-finite score: {row}")
            row["n_people"] = int(row["n_people"])
            if row["n_people"] < 2 or not row["ci_low"] <= row["mean"] <= row["ci_high"]:
                raise ValueError(f"Invalid participant interval: {row}")
        for row in curves:
            row['train_people'] = int(row['train_people'])
            duration = float(row['target_seconds_per_person'])
            if row['train_people'] < 1 or not math.isfinite(duration) or duration <= 0:
                raise ValueError(f"Invalid learning-curve training axis: {row}")
        for name in data.get("source_files", []):
            p = source_path(name)
            if not p.is_file():
                raise ValueError(f"Missing provenance file: {p}")
            provenance.append({"path": str(p), "sha256": sha(p)})
    if final:
        for key in ("results_reviewed", "natview_reviewed", "evidence_reviewed"):
            if data.get(key) is not True:
                raise ValueError(f"Final poster requires {key}=true after review")
        if data.get("status") != "completed":
            raise ValueError("Final poster requires status=completed")
        if not data.get("completed_jobs") or any(not j.get('job_id') or j.get("state") != "COMPLETED" for j in data["completed_jobs"]):
            raise ValueError("Final poster requires completed M3 job evidence")
        for key in ("experiment_note", "reviewed_report"):
            if not data.get(key) or not source_path(data[key]).is_file():
                raise ValueError(f"Final poster requires an existing {key}")
            p = source_path(data[key])
            provenance.append({"path": str(p), "sha256": sha(p)})
        report=source_path(data['reviewed_report'])
        if re.search(r'\b(?:DRAFT|PENDING)\b',report.read_text(encoding='utf-8-sig')):
            raise ValueError('Reviewed report still contains DRAFT/PENDING release markers')
        if data.get('reviewed_report_sha256') and sha(report)!=data['reviewed_report_sha256']:
            raise ValueError('Reviewed report changed after its final review hash was recorded')
        for key in ("protocol_caption", "result_caption", "result_takeaway", "result_scope", "primary_view"):
            if not data.get(key):
                raise ValueError(f"Final poster requires {key}")
        if not 2 <= len(rows) <= 5:
            raise ValueError("Final primary_view must select 2-5 directly comparable rows")
        if len(curves) < 2:
            raise ValueError("Final poster requires completed learning/comparison rows, not a pending panel")
        if len({(r['condition'], r['target'], r['metric']) for r in rows}) != 1:
            raise ValueError("Primary figure cannot mix conditions, targets or metrics")
        if len({r['model'] for r in rows}) != len(rows):
            raise ValueError("Primary figure has repeated model rows; narrow primary_view")
        if data.get('panel_selection_id')!='EC_regional64_predeclared_20261021':
            raise ValueError('Final poster requires the recorded predeclared panel selection')
        panel=data.get('natview_panel')
        if not panel or panel.get('outcome') not in ('prediction','qc_failure'):
            raise ValueError('Final poster needs reviewed NATVIEW prediction or an honest completed QC failure')
        if panel.get('n_reserved_people')!=8 or panel.get('pilot_excluded') is not True:
            raise ValueError('NATVIEW must retain all-eight accounting and exclude the ingestion pilot')
        if int(panel['n_accepted_people'])+int(panel['n_failed_people'])!=8:
            raise ValueError('NATVIEW acceptance/failure counts must account for all eight reserved people')
        if panel.get('v1_accepted_people')!=1 or panel.get('amendment_role')!='secondary exploratory after QC':
            raise ValueError('Preserve strict v1 QC and amended-v2 exploratory scope')
        if not panel.get('coverage_caption') or not panel.get('montage_caption'):
            raise ValueError('NATVIEW requires all-eight coverage and the interpolated target-site policy')
        for key in ('natview_summary','natview_note'):
            if not data.get(key) or not source_path(data[key]).is_file():
                raise ValueError(f'Final poster requires existing {key}')
            pp=source_path(data[key]);provenance.append(dict(path=str(pp),sha256=sha(pp)))
        ns=read_json(source_path(data['natview_summary']))
        if not (ns.get('complete') is True or ns.get('status')=='completed' or
                (ns.get('completed_utc') and ns.get('branch')=='amended_v2_secondary_complete_eligible_panel')):
            raise ValueError('NATVIEW source summary must record completion, including any QC failure')
        if panel['outcome']=='prediction':
            if int(panel['n_people'])<2 or not panel['ci_low']<=panel['mean']<=panel['ci_high']:
                raise ValueError('Invalid separate NATVIEW participant interval')
    return data, rows, curves, provenance


class Poster:
    def __init__(self, path, final):
        self.c = Canvas(str(path), pagesize=(W, H), pageCompression=1,
                        initialFontName='Body', initialFontSize=36)
        self.c.setTitle("Clinical EEG-to-fMRI feasibility: PhD thesis exploration")
        self.c.setAuthor("Seamus Taylor")
        self.c.setSubject("PhD exploration; " + ("reviewed exploratory results" if final else "INTERNAL DRAFT - results pending"))
        self.c.setCreator("ReportLab; measured example2.pdf layout")
        self.boxes, self.words = [], []

    def rect(self, x, y, w, h, color=None, stroke=None, lw=5):
        self.c.setLineWidth(lw)
        self.c.setFillColor(colors.HexColor(color or "#FFFFFF"))
        self.c.setStrokeColor(colors.HexColor(stroke or "#FFFFFF"))
        self.c.rect(x, H-y-h, w, h, fill=int(color is not None), stroke=int(stroke is not None))

    def line(self, x1, y1, x2, y2, color=MUTED, lw=3):
        self.c.setStrokeColor(colors.HexColor(color))
        self.c.setLineWidth(lw)
        self.c.line(x1, H-y1, x2, H-y2)

    def para(self, text, x, y, w, size=36, leading=None, color=INK,
             font="Body", align=TA_LEFT, max_h=None, role="body"):
        style = ParagraphStyle("p", fontName=font, fontSize=size, leading=leading or size*1.2,
                               textColor=colors.HexColor(color), alignment=align)
        p = Paragraph(text, style)
        _, h = p.wrap(w, H)
        if max_h is not None and h > max_h+.1:
            raise ValueError(f"Text overflow {h:.1f}>{max_h:.1f}: {text[:100]}")
        if x < 0 or y < 0 or x+w > W+.1 or y+h > H+.1:
            raise ValueError(f"Text outside page: {text[:70]}")
        p.drawOn(self.c, x, H-y-h)
        self.boxes.append(dict(x=x,y=y,w=w,h=h,font=font,size=size,role=role,text=text))
        self.words.append(re.sub("<[^>]+>", " ", text))
        return h

    def label(self, text, x, y, size=28, color=MUTED, bold=False):
        width = pdfmetrics.stringWidth(text, "Body-Bold" if bold else "Body", size)
        return self.para(escape(text), x, y, width+2, size=size, color=color,
                         font="Body-Bold" if bold else "Body", role="figure_label")

    def section(self, name, title, color=BLUE):
        x,y,w,h=GEOMETRY[name]
        self.rect(x,y,w,h,stroke=color,lw=5 if color==BLUE else 6)
        self.para(title,x+23,y+17,w-46,size=48,font="Display",color=color,max_h=120,role="heading")
        return x,y,w,h

    def arrow(self, x1,y1,x2,y2,color=BLUE,lw=4):
        self.line(x1,y1,x2,y2,color,lw)
        angle=math.atan2(y2-y1,x2-x1)
        for a in (angle-.47,angle+.47):
            self.line(x2,y2,x2-16*math.cos(a),y2-16*math.sin(a),color,lw)

    def node(self,text,x,y,w,h,size=29,color=BLUE):
        self.rect(x,y,w,h,color="#F1F8FD",stroke=color,lw=2.5)
        self.para(text,x+9,y+10,w-18,size=size,leading=size*1.13,align=TA_CENTER,
                  max_h=h-15,role="diagram")

    def architecture(self):
        x,y,w,h=self.section("architecture","Model architecture")
        # Simplified UnEBOLT paper, section 2.2; no new layer counts or details.
        self.para("UnEBOLT schematic [1]",x+23,y+102,w-46,size=29,
                  color=MUTED,max_h=40,role="caption")
        nodes=[(155,91,"EEG history<br/>preceding each BOLD frame"),
               (289,122,"<b>Shared EEG encoder</b><br/>Temporal + spectral<br/>Gated fusion"),
               (454,117,"ROI embeddings +<br/>representation adapter<br/>ROI-specific heads"),
               (614,89,"Regional BOLD estimates<br/>over successive frames")]
        for i,(yy,hh,txt) in enumerate(nodes):
            self.node(txt,x+28,y+yy,w-56,hh,size=29)
            if i<len(nodes)-1:
                self.arrow(x+w/2,y+yy+hh,x+w/2,y+nodes[i+1][0]-6)
        self.para("Published reference; not tested here.<br/>Patient BOLD/utility unvalidated.",
                  x+23,y+727,w-46,size=25,leading=29,max_h=76,color=MUTED,role="caption")

    def clinical_path(self):
        x,y,w,h=GEOMETRY["clinical_path"]
        for i,txt in enumerate(("Offline prediction","Frozen external test","Silent prospective study")):
            self.node(txt,x,y+i*116,w,82,size=29)
            if i<2:self.arrow(x+w/2,y+i*116+82,x+w/2,y+i*116+112)
        self.para("Proposed validation pathway",x,y+321,w,size=25,align=TA_CENTER,
                  color=MUTED,role="caption")

    def pending(self,x,y,w,h,title,body):
        self.rect(x,y,w,h,color="#F5F7F9",stroke=GRID,lw=2)
        self.para(title,x+23,y+28,w-46,size=39,font="Body-Bold",align=TA_CENTER,max_h=105,color=MUTED)
        self.para(body,x+37,y+146,w-74,size=31,align=TA_CENTER,max_h=h-163,color=MUTED)

    def scores(self,rows,data):
        x,y,w,h=GEOMETRY["results"]
        self.para("New M3 empirical evidence",x,y+15,w,size=48,font="Display",max_h=65,role="heading")
        if not rows:
            self.pending(x,y+92,w,319,"RESULTS PENDING",
                         "Completed participant-level estimates will appear here.<br/>"
                         "No interim, simulated or earlier-project scores are plotted.")
            return
        self.para('EC-trained/test-EC | 12 training people x 240 target-s | regional64',
                  x,y+76,w,size=24,color=MUTED,max_h=30,role='caption')
        px=x+465; pw=w-555; py=y+115; ph=212
        lo=math.floor(min(0,min(r['ci_low'] for r in rows))*10)/10
        hi=max(lo+.1,math.ceil(max(r['ci_high'] for r in rows)*10)/10)
        sx=lambda z:px+pw*(z-lo)/(hi-lo)
        for i in range(round((hi-lo)*10)+1):
            v=lo+i*.1
            self.line(sx(v),py,sx(v),py+ph,GRID,1.5)
            self.label(f"{v:.1f}",sx(v)-22,py+ph+12,size=25)
        for i,r in enumerate(rows):
            yy=py+25+i*(ph-40)/max(1,len(rows)-1)
            color=BLUE if i%2 else ORANGE
            label=r.get('label') or r['model']
            self.para(escape(label),x,yy-17,450,size=30,max_h=40)
            self.line(sx(r['ci_low']),yy,sx(r['ci_high']),yy,color,5)
            self.c.setFillColor(colors.HexColor(color))
            self.c.circle(sx(r['mean']),H-yy,8,fill=1,stroke=0)
            self.para(f"{r['mean']:.3f}",x+w-84,yy-17,84,size=28,max_h=37)
        self.para(escape(data.get('metric_label',rows[0]['metric']))+" (95% CI over people)",
                  px,py+ph+51,pw,size=26,align=TA_CENTER,max_h=35,color=MUTED,role="caption")
        self.para(escape(data.get('result_caption','')),x,y+425,w,size=25,max_h=32,
                  leading=29,color=MUTED,role="caption")

    def learning(self,curves,data):
        x,y,w,h=GEOMETRY['learning']
        self.para("People and retained target time",x,y,w,size=46,font="Body-Bold",max_h=60,role="heading")
        if not curves:
            self.pending(x,y+86,w,343,"LEARNING COMPARISON PENDING",
                         "ds006040: Ridge EEG, 4/12 training people and 120/240 retained target-seconds/person. "
                         "Same held-out EC evaluation; exploratory development evidence.")
            self.natview(data.get('natview_panel'))
            return
        if len({(r['condition'],r['target'],r['metric']) for r in curves})!=1:
            raise ValueError("Learning figure must have one condition, target and metric")
        # Each line is one exact model/duration; no pooling of independent axes.
        groups={}
        for r in curves:
            key=(r['model'],str(r['target_seconds_per_person']))
            groups.setdefault(key,[]).append(r)
        if len(groups)>2:raise ValueError("Predeclared learning figure has two duration series")
        self.para(escape(data.get('learning_scope','ds006040 | EC-trained/test-EC | regional64 temporal r')),
                  x,y+65,w,size=25,color=MUTED,max_h=34,role='caption')
        px=x+100;py=y+120;pw=w-125;ph=196
        xs=[int(r['train_people']) for r in curves]
        lo=math.floor(min(0,min(r['ci_low'] for r in curves))*20)/20
        hi=max(lo+.05,math.ceil(max(r['ci_high'] for r in curves)*20)/20)
        sx=lambda n:px+pw*(n-min(xs))/max(1,max(xs)-min(xs))
        sy=lambda z:py+ph*(1-(z-lo)/(hi-lo))
        for i in range(round((hi-lo)*20)+1):
            v=lo+i*.05
            self.line(px,sy(v),px+pw,sy(v),GRID,1.5)
            self.label(f"{v:.2f}",x,sy(v)-14,size=25)
        for xx in sorted(set(xs)):
            self.label(str(xx),sx(xx)-13,py+ph+9,size=27)
        for i,(key,rr) in enumerate(groups.items()):
            rr=sorted(rr,key=lambda r:int(r['train_people']))
            color=(ORANGE,BLUE,"#555555","#7B5B9A")[i]
            for a,b in zip(rr,rr[1:]):self.line(sx(int(a['train_people'])),sy(a['mean']),sx(int(b['train_people'])),sy(b['mean']),color,4)
            for r in rr:
                xx=sx(int(r['train_people'])); yy=sy(r['mean'])
                self.line(xx,sy(r['ci_low']),xx,sy(r['ci_high']),color,3)
                self.c.setFillColor(colors.HexColor(color));self.c.circle(xx,H-yy,7,fill=1,stroke=0)
            self.line(x+16+i*448,y+408,x+68+i*448,y+408,color,4)
            self.label(f"{key[1]} target-s/person",x+80+i*448,y+393,size=25)
        self.para("Training people (fixed evaluation)",px,py+ph+47,pw,size=28,align=TA_CENTER,max_h=37,role="caption")
        self.para(escape(data.get('learning_caption','Person-bootstrap 95% intervals; fixed subsets and one seed.')),
                  x,y+426,w,size=24,leading=28,max_h=33,color=MUTED,role="caption")
        self.natview(data.get('natview_panel'))

    def natview(self,panel):
        """Separate protocol, N, axis and interval; never pooled with development."""
        x,y,w,h=GEOMETRY['natview_inset']
        self.rect(x,y,w,h,color='#F5FAFD',stroke=BLUE,lw=2.5)
        self.para('NATVIEW: transfer and QC',x+20,y+12,w-40,size=34,
                  font='Body-Bold',max_h=44,role='heading')
        if not panel:
            self.para('Strict v1 QC: 1/8; amended v2 QC: 6/8.',x+20,y+66,w-40,size=27,
                      color=MUTED,max_h=38)
            self.para('v2 is secondary exploratory after QC; pilot excluded. '
                      'Two failures/8 (<60 frames). Accuracy review pending.',x+20,y+115,w-40,
                      size=27,leading=32,max_h=97)
            self.para('23 target sites include interpolation; VU ridge frozen. '
                      'Final all-eight frame coverage pending.',
                      x+20,y+218,w-40,size=25,leading=29,max_h=58,color=MUTED,role='caption')
            return
        if panel.get('outcome')=='qc_failure':
            self.para(escape(panel['scope']),x+20,y+63,w-40,size=27,leading=31,max_h=63)
            self.para(escape(panel['failure_caption']),x+20,y+137,w-40,size=27,leading=31,max_h=65)
            self.para(escape(panel['qc_caption']),x+20,y+212,w-40,size=25,leading=29,
                      max_h=58,color=MUTED,role='caption')
            return
        self.para(f"Strict timing {panel['v1_accepted_people']}/8; amended QC {panel['n_accepted_people']}/8."
                  f"<br/>Secondary exploratory; n={panel['n_people']}; pilot excluded.",
                  x+20,y+63,w-40,size=25,leading=29,max_h=58,
                  color=MUTED,role='caption')
        # The NATVIEW estimate owns its own numeric scale and participant count.
        low,mean,high=[float(panel[k]) for k in ('ci_low','mean','ci_high')]
        ax0,ax1=min(-.05,low-.04),max(.1,high+.04)
        px=x+440;pw=w-500;yy=y+145
        sx=lambda z:px+pw*(z-ax0)/(ax1-ax0)
        self.para(f"Regional r {mean:.3f}<br/>95% CI [{low:.4f}, {high:.3f}]",
                  x+20,yy-18,400,size=25,leading=29,max_h=60)
        self.line(px,yy,px+pw,yy,GRID,2)
        self.line(sx(low),yy,sx(high),yy,BLUE,5)
        self.c.setFillColor(colors.HexColor(BLUE));self.c.circle(sx(mean),H-yy,7,fill=1,stroke=0)
        for v in (ax0,(ax0+ax1)/2,ax1):
            self.label(f'{v:.2f}',sx(v)-25,yy+18,size=23)
        self.para(escape(panel['coverage_caption'])+'<br/>'+escape(panel['montage_caption']),x+20,y+204,w-40,size=25,
                  leading=29,max_h=59,color=MUTED,role='caption')


def build(out, content, data, rows, curves, final):
    p=Poster(out,final)
    p.rect(0,0,W,H,color="#FFFFFF")
    p.rect(*GEOMETRY['title'],color=BLUE)
    for text,yy in (("Clinical EEG-to-fMRI feasibility",84),("PhD thesis exploration",202)):
        p.para(text,102,yy,W-204,size=84,leading=100,font="Display",color="#FFFFFF",
               align=TA_CENTER,max_h=102,role="title")
    p.para(("INTERNAL DRAFT - final report review pending" if data.get('natview_panel') else
            "INTERNAL DRAFT - NATVIEW and final report review pending" if rows else
            "INTERNAL DRAFT - M3 results and evidence review pending") if not final else
           "Exploratory research | reviewed M3 experiments | 21 October 2026",
           727,320,1556,size=23,leading=27,max_h=28,color=MUTED,align=TA_CENTER,role="status")
    x,y,w,h=p.section('problem','The clinical question')
    p.para(content['problem'],x+23,y+140,w-46,size=36,max_h=h-150)
    p.architecture()
    x,y,w,h=p.section('aim','A computer science thesis to explore')
    p.para(content['aim'],x+23,y+98,w-46,size=36,leading=44,max_h=h-114)
    x,y,w,h=p.section('hypothesis','Working hypothesis')
    p.para(content['hypothesis'],x+23,y+92,w-46,size=36,leading=43,max_h=h-107)
    p.clinical_path()
    x,y,w,h=p.section('models','Models and possible uses')
    p.para('Healthy technical BOLD evidence; uses proposed',x+23,y+83,w-46,
           size=25,color=MUTED,max_h=33,role='caption')
    for txt,yy,mh in zip(content['models'],(122,188,282),(66,96,66)):
        p.para(txt,x+23,y+yy,w-46,size=27,leading=30,max_h=mh)
    p.para('Reported temporal r; different protocols, not a ranking.',x+23,y+355,w-46,
           size=23,color=MUTED,max_h=29,role='caption')
    p.rect(*GEOMETRY['divider'],color=ORANGE)
    p.para('M3 evidence and proposed PhD next steps',80,1684,W-160,size=56,
           font='Display',color='#FFFFFF',align=TA_CENTER,max_h=72,role='heading')
    x,y,w,h=p.section('methods','M3 study design',ORANGE)
    method=data.get('methods_text') or content['methods']
    p.para(method,x+23,y+100,w-46,size=35,leading=42,max_h=h-115)
    p.scores(rows,data)
    # This narrow interstitial area exists in the source between box and figure.
    p.para(escape(data.get('result_takeaway','The first test is whether added information or capacity improves held-out prediction.')),
           96.423,2322,920.102,size=31,leading=37,max_h=104,color=MUTED)
    p.learning(curves,data)
    x,y,w,h=p.section('work_packages','Three proposed work packages',ORANGE)
    offset=94
    for title,txt in content['work_packages']:
        hh=p.para(f'<b>{title}</b> {txt}',x+23,y+offset,w-46,size=33,leading=39,max_h=100)
        offset+=hh+13
    x,y,w,h=p.section('clinical_gate','Clinical uses and limits',ORANGE)
    p.para(content['clinical_gate'],x+23,y+96,w-46,size=34,leading=41,max_h=288)
    p.para(content['references'],x+23,y+386,w-46,size=24,leading=29,max_h=90,color=MUTED,role='references')
    p.para('Seamus Taylor | PhD thesis exploration',96,3265,W-192,size=48,
           font='Display',color=BLUE,align=TA_CENTER,max_h=65,role='author')
    p.c.showPage();p.c.save()
    return p


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--out',type=Path,default=ROOT/'output/pdf/EEG_fMRI_thesis_exploration_poster_A0.pdf')
    a.add_argument('--content',type=Path,default=ASSETS/'content.json')
    a.add_argument('--inputs',type=Path,default=ASSETS/'integration.json')
    a.add_argument('--reference-pdf',type=Path,default=ASSETS/'reference/example2.pdf',
                   help='Optional private reference; if absent, use recorded geometry/hash without loading it')
    a.add_argument('--audit-native',action='store_true',help='Check native exports/preselection without authoring a PDF')
    a.add_argument('--audit-natview',action='store_true',help='Check NATVIEW person means, coverage, QC and frozen hashes without PDF authoring')
    a.add_argument('--final',action='store_true',help='Require completed M3 jobs, reviewed results and reviewed evidence')
    a.add_argument('--validate-only',action='store_true',help='Validate input contract without authoring a PDF')
    args=a.parse_args()
    reference=reference_provenance(args.reference_pdf)
    if args.audit_natview:
        nv=natview_adapter(ROOT/'reports/thesis_exploration/natview/v2/machine_summary.json',
                           ROOT/'reports/thesis_exploration/natview/v2/per_person_metrics.csv')
        (ASSETS/'natview_audit.json').write_text(json.dumps(nv,indent=2),encoding='utf-8')
        print('NATVIEW verified: six person means; 740/2304 frames; all-eight QC partition; strict/amended and frozen-model provenance.');return
    if args.audit_native:
        audit=native_adapter(ROOT/'reports/thesis_exploration/data/summary.json',
                             ROOT/'reports/thesis_exploration/data/per_person_scores.csv',
                             ROOT/'reports/thesis_exploration/data/protocol.json')
        (ASSETS/'native_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
        print('Native preselection verified against protocol and per-person CSV; 4 primary and 4 learning points.');return
    content=read_json(args.content)
    data,rows,curves,provenance=inputs(args.inputs,args.final)
    if args.validate_only:
        print(json.dumps(dict(final=args.final,rows=len(rows),curves=len(curves),reference=reference,sources=provenance),indent=2));return
    fonts();args.out.parent.mkdir(parents=True,exist_ok=True)
    p=build(args.out,content,data,rows,curves,args.final)
    count=len(re.findall(r"\b[\w'-]+\b",' '.join(p.words)))
    if count > 1000:
        raise ValueError(f'Poster exceeds 1000-word maximum: {count}')
    manifest=dict(status='reviewed exploratory poster' if args.final else 'internal draft - pending NATVIEW/final evidence',
                  **reference,
                  page_points=[W,H],geometry_points_top_origin=GEOMETRY,word_count=count,
                  content_sha256=sha(args.content),source_files=provenance,text_boxes=p.boxes,
                  input_manifest=str(args.inputs),input_manifest_sha256=sha(args.inputs) if args.inputs.exists() else None,
                  results_rows=rows,learning_rows=curves,natview_panel=data.get('natview_panel'),pdf_sha256=sha(args.out),
                  result_scope=data.get('result_scope'),protocol_caption=data.get('protocol_caption'))
    (ASSETS/'build_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'Built {args.out}\nWords: {count}; primary rows: {len(rows)}; curve rows: {len(curves)}')


if __name__=='__main__':main()
