#!/usr/bin/env python3
"""Build the visually revised poster from the reviewed evidence exports.

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
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "reports/thesis_exploration/poster"
REFERENCE_ID = 'Examples.zip/Files/example2.pdf'
# Verified from the supplied PDF and the first measured-layout build manifest.
REFERENCE_SHA256 = '6cbcaa767705fab9f998e7bfbe85e27b66d7da3c3dcd356359c5c3fd43cd6e83'
W, H = 2383.937, 3370.394
BLUE, ORANGE = "#00A2FF", "#FF9300"
INK, MUTED, GRID = "#102A43", "#4C6172", "#D9E5ED"
GEOMETRY = {'title': [56.69287, 56.693, 2270.55113, 450.0],
 'problem': [96.42254, 565.0, 563.5692, 300.0],
 'architecture': [96.42254, 900.0, 563.5692, 710.0],
 'results': [727.6812, 565.0, 1556.084, 795.0],
 'takeaway': [727.6812, 1390.0, 1556.084, 220.0],
 'divider': [56.69287, 1665.627, 2270.55113, 102.619],
 'learning': [96.42254, 1820.803, 920.1018, 475.0],
 'methods': [96.42254, 2325.0, 920.1018, 307.0],
 'natview_inset': [96.42254, 2662.0, 920.1018, 478.0],
 'work_packages': [1078.925, 1820.803, 1204.341, 570.0],
 'models': [1078.925, 2420.0, 1204.341, 285.0],
 'clinical_gate': [1078.925, 2735.0, 1204.341, 405.0],
 'references': [96.42254, 3180.0, 2187.0, 95.0],
 'author': [96.42254, 3291.0]}


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
        status='local bytes verified; measured canvas and asymmetric grid adapted in visual revision'
    else:
        status='not loaded; recorded verified SHA256; measured canvas and asymmetric grid adapted'
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
    """Vector-only A0 poster with a results-first visual hierarchy."""

    def __init__(self, path, final):
        self.c = Canvas(str(path), pagesize=(W, H), pageCompression=1,
                        initialFontName='Body', initialFontSize=34)
        self.c.setTitle('Can EEG recover clinically useful fMRI?')
        self.c.setAuthor('Seamus Taylor')
        self.c.setSubject('Computer science PhD exploration; reviewed exploratory M3 evidence')
        self.c.setCreator('ReportLab; visual revision of the measured example2 layout')
        self.boxes, self.words = [], []

    def rect(self, x, y, w, h, color=None, stroke=None, lw=2, radius=0):
        self.c.setLineWidth(lw)
        self.c.setFillColor(colors.HexColor(color or '#FFFFFF'))
        self.c.setStrokeColor(colors.HexColor(stroke or '#FFFFFF'))
        args=(x,H-y-h,w,h)
        if radius:
            self.c.roundRect(*args,radius,fill=int(color is not None),stroke=int(stroke is not None))
        else:
            self.c.rect(*args,fill=int(color is not None),stroke=int(stroke is not None))

    def line(self, x1,y1,x2,y2,color=MUTED,lw=3):
        self.c.setStrokeColor(colors.HexColor(color));self.c.setLineWidth(lw)
        self.c.line(x1,H-y1,x2,H-y2)

    def circle(self,x,y,r,color,stroke=None,lw=2):
        self.c.setFillColor(colors.HexColor(color));self.c.setLineWidth(lw)
        self.c.setStrokeColor(colors.HexColor(stroke or color))
        self.c.circle(x,H-y,r,fill=1,stroke=int(stroke is not None))

    def para(self,text,x,y,w,size=34,leading=None,color=INK,font='Body',
             align=TA_LEFT,max_h=None,role='body'):
        style=ParagraphStyle('p',fontName=font,fontSize=size,leading=leading or size*1.2,
                             textColor=colors.HexColor(color),alignment=align)
        p=Paragraph(text,style);_,h=p.wrap(w,H)
        if max_h is not None and h>max_h+.1:
            raise ValueError(f'Text overflow {h:.1f}>{max_h:.1f}: {text[:100]}')
        if x<0 or y<0 or x+w>W+.1 or y+h>H+.1:
            raise ValueError(f'Text outside page: {text[:70]}')
        p.drawOn(self.c,x,H-y-h)
        self.boxes.append(dict(x=x,y=y,w=w,h=h,font=font,size=size,role=role,text=text))
        self.words.append(re.sub('<[^>]+>',' ',text))
        return h

    def label(self,text,x,y,size=26,color=MUTED,bold=False):
        font='Body-Bold' if bold else 'Body'
        width=pdfmetrics.stringWidth(text,font,size)
        return self.para(escape(text),x,y,width+2,size=size,color=color,font=font,role='figure_label')

    def arrow(self,x1,y1,x2,y2,color=BLUE,lw=4):
        self.line(x1,y1,x2,y2,color,lw)
        angle=math.atan2(y2-y1,x2-x1)
        for a in (angle-.47,angle+.47):
            self.line(x2,y2,x2-15*math.cos(a),y2-15*math.sin(a),color,lw)

    def card(self,name,accent=BLUE,fill='#FFFFFF'):
        x,y,w,h=GEOMETRY[name]
        self.rect(x+5,y+6,w,h,color='#E4EDF4',radius=14)
        self.rect(x,y,w,h,color=fill,stroke='#D8E4ED',lw=1.5,radius=14)
        self.rect(x,y+19,7,h-38,color=accent)
        return x,y,w,h

    def heading(self,text,x,y,w,size=42,color=INK):
        return self.para(text,x,y,w,size=size,leading=size*1.14,font='Display',
                         color=color,max_h=size*2.3,role='heading')

    def kicker(self,text,x,y,w,color=BLUE):
        self.para(text,x,y,w,size=25,leading=30,color=color,font='Body-Bold',max_h=32,role='kicker')

    def trace(self,x,y,w,h,color,kind='eeg',lw=4):
        """Decorative schematic, deliberately never presented as measured data."""
        pts=[]
        for i in range(181):
            u=i/180
            if kind=='eeg':
                z=.48*math.sin(19*math.pi*u)+.23*math.sin(49*math.pi*u)+.14*math.cos(77*math.pi*u)
                z*=.65+.35*math.sin(3*math.pi*u)**2
            else:
                z=.65*math.sin(2.6*math.pi*u-.6)+.2*math.cos(5*math.pi*u)
            pts.append((x+u*w,y+z*h/2))
        path=self.c.beginPath();path.moveTo(pts[0][0],H-pts[0][1])
        for xx,yy in pts[1:]:path.lineTo(xx,H-yy)
        self.c.setStrokeColor(colors.HexColor(color));self.c.setLineWidth(lw);self.c.drawPath(path)

    def hero_art(self):
        # Abstract, original vector rendering: EEG and slower regional outputs.
        x,y,w=1770,105,475
        self.para('EEG HISTORY',x,y,w,size=23,color='#A9DFFF',font='Body-Bold',max_h=30)
        for i in range(3):self.trace(x,y+65+i*34,w,30,('#54CBFF','#FFFFFF','#54CBFF')[i],lw=3)
        self.arrow(x+w/2,y+160,x+w/2,y+202,color=ORANGE,lw=4)
        self.rect(x,y+219,w,101,color='#1C3F5B',radius=14)
        for i in range(3):self.trace(x+20,y+245+i*24,w-40,21,('#66D5FF','#FFB854','#FFFFFF')[i],kind='bold',lw=3.5)
        self.para('REGIONAL BOLD ESTIMATES',x,y+337,w,size=22,color='#A9DFFF',
                  font='Body-Bold',max_h=28)
        self.para('Schematic; not recorded signals',x,y+368,w,size=20,color='#B9CFDF',max_h=27,role='caption')

    def architecture(self):
        x,y,w,h=self.card('architecture')
        self.kicker('METHOD / THE ACTUAL M3 PIPELINE',x+27,y+23,w-54)
        self.heading('How EEG becomes a prediction',x+27,y+62,w-54,size=39)
        self.para('Past EEG is summarized before fitting either model.',x+27,y+164,w-54,
                  size=25,leading=30,max_h=61,color=MUTED,role='caption')
        nodes=[('24 seconds of EEG','5 scalp groups x 5 frequency bands'),
               ('300 power features','12 lags; training-only standardization'),
               ('Ridge or small MLP','Same EEG features; inner tuning'),
               ('Predict BOLD targets','Score 64 regional series here')]
        for i,(title,body) in enumerate(nodes):
            yy=y+237+i*103
            fill='#EAF6FF' if i<3 else '#FFF1DF'
            self.rect(x+28,yy,w-56,88,color=fill,radius=10)
            self.para(f'<b>{title}</b><br/>{body}',x+43,yy+10,w-86,size=27,leading=31,
                      max_h=66,align=TA_CENTER,role='diagram')
            if i<3:self.arrow(x+w/2,yy+89,x+w/2,yy+101,lw=3)
        self.para('MLP learns four target groups. Published models were not reproduced.',
                  x+28,y+647,w-56,size=25,leading=29,max_h=60,color=MUTED,role='caption')

    def scores(self,rows,data):
        x,y,w,h=self.card('results')
        self.kicker('01 / EVIDENCE FROM M3',x+32,y+23,w-64)
        self.heading('Ridge leads the matched-feature models',x+32,y+69,w-64,size=49)
        self.para('ds006040 development | EC-trained / EC-tested | 64 regional targets',
                  x+32,y+141,w-64,size=28,color=MUTED,max_h=38,role='caption')
        for i,(value,caption) in enumerate((('27','held-out people'),('96','fitted experiment cells'),('300','matched EEG-power features'))):
            xx=x+32+i*498
            self.para(value,xx,y+209,215,size=79,leading=84,font='Display',max_h=90)
            self.para(caption,xx+205,y+224,258,size=28,leading=33,color=MUTED,max_h=70)
        self.line(x+32,y+322,x+w-32,y+322,GRID,2)
        px=x+535;pw=w-735;py=y+370;ph=258
        lo,hi=-.05,.25
        sx=lambda z:px+pw*(z-lo)/(hi-lo)
        for v in (-.05,0,.05,.10,.15,.20,.25):
            self.line(sx(v),py-4,sx(v),py+ph+4,('#98AEBF' if v==0 else GRID),2 if v==0 else 1.4)
            self.label(f'{v:.2f}',sx(v)-26,py+ph+22,size=25)
        for i,r in enumerate(rows):
            yy=py+27+i*70
            if i==0:self.rect(x+22,yy-30,w-44,61,color='#EAF6FF',radius=7)
            color=BLUE if i==0 else ('#7190A6' if i==1 else ORANGE if i==2 else '#344F67')
            self.para(escape(r.get('label') or r['model']),x+34,yy-24,470,
                      size=34,max_h=45,font='Body-Bold' if i==0 else 'Body')
            self.line(sx(r['ci_low']),yy,sx(r['ci_high']),yy,color,7)
            for v in ('ci_low','ci_high'):self.line(sx(r[v]),yy-7,sx(r[v]),yy+7,color,3)
            self.circle(sx(r['mean']),yy,10,color,stroke='#FFFFFF',lw=2)
            self.para(f"{r['mean']:.3f}",x+w-161,yy-27,126,size=39,
                      color=color,font='Body-Bold',max_h=50)
        self.para('Mean regional temporal r | 95% CI across people',px,py+ph+67,pw,
                  size=26,align=TA_CENTER,color=MUTED,max_h=35,role='caption')
        self.para('12 training people x 240 retained target-seconds/person. EEG ridge predictive R² = .028.',
                  x+32,y+738,w-64,size=26,leading=31,color=MUTED,max_h=45,role='caption')

    def learning(self,curves,data):
        x,y,w,h=self.card('learning')
        self.kicker('02 / EFFECT OF TRAINING DATA',x+27,y+21,w-54)
        self.heading('People and recording time help',x+27,y+60,w-54,size=39)
        self.para('Ridge EEG | same held-out EC evaluation | n=27',x+27,y+112,w-54,
                  size=26,color=MUTED,max_h=35,role='caption')
        px=x+107;py=y+177;pw=w-170;ph=185
        sx=lambda n:px+pw*(n-4)/8
        sy=lambda v:py+ph*(1-v/.25)
        for v in (0,.05,.10,.15,.20,.25):
            self.line(px,sy(v),px+pw,sy(v),GRID,1.4)
            self.label(f'{v:.2f}',x+25,sy(v)-15,size=25)
        groups={}
        for r in curves:groups.setdefault(int(r['target_seconds_per_person']),[]).append(r)
        for duration,rr in sorted(groups.items()):
            rr=sorted(rr,key=lambda r:r['train_people']);color=ORANGE if duration==120 else BLUE
            a,b=rr;self.line(sx(a['train_people']),sy(a['mean']),sx(b['train_people']),sy(b['mean']),color,5)
            for r in rr:
                xx=sx(r['train_people']);yy=sy(r['mean'])
                self.line(xx,sy(r['ci_low']),xx,sy(r['ci_high']),color,2.7)
                self.circle(xx,yy,7,color)
        for n in (4,12):self.label(f'{n} people',sx(n)-(32 if n==4 else 107),py+ph+8,size=25)
        self.para('Regional r; 95% person-bootstrap CIs.',x+107,y+148,w-170,size=23,color=MUTED,max_h=28,role='caption')
        for i,(duration,color) in enumerate(((120,ORANGE),(240,BLUE))):
            xx=x+27+i*443;self.line(xx,y+438,xx+45,y+438,color,5)
            self.label(f'{duration} target-s/person',xx+57,y+421,size=25)

    def natview(self,panel):
        x,y,w,h=self.card('natview_inset',accent=ORANGE,fill='#FFF8F0')
        self.kicker('EXTERNAL DATA / SECONDARY EXPLORATION',x+27,y+23,w-54,color='#9B5700')
        self.heading('NATVIEW: transfer remains weak',x+27,y+65,w-54,size=38)
        self.para('Strict timing QC: 1/8. Amended QC: 6/8; n=6.<br/>Metadata-only amendment; ingestion pilot excluded.',
                  x+27,y+118,w-54,size=26,leading=31,max_h=64,color=MUTED,role='caption')
        self.para(f"{panel['mean']:.3f}",x+27,y+203,370,size=86,leading=91,font='Display',max_h=96)
        self.para('regional r',x+34,y+298,340,size=27,max_h=36)
        self.para(f"{panel['predictive_R2']:.3f}",x+483,y+203,390,size=76,leading=91,
                  font='Display',color='#A05A14',max_h=96)
        self.para('predictive R²',x+489,y+298,360,size=27,max_h=36)
        self.para(f"r: 95% CI [{panel['ci_low']:.4f}, {panel['ci_high']:.3f}]; includes zero.",
                  x+27,y+337,w-54,size=26,color=MUTED,max_h=35,role='caption')
        frac=panel['scored_frames']/panel['total_frames']
        self.rect(x+27,y+379,w-54,12,color='#E6D9CB',radius=6)
        self.rect(x+27,y+379,(w-54)*frac,12,color=ORANGE,radius=6)
        self.para(f"{panel['scored_frames']}/{panel['total_frames']} frames scored ({100*frac:.1f}% of all eight).",
                  x+27,y+400,w-54,size=25,max_h=33,color=MUTED,role='caption')
        self.para('Frozen VU model/QC; 23 target sites include interpolation.',x+27,y+436,w-54,
                  size=24,max_h=31,color=MUTED,role='caption')


def build(out,content,data,rows,curves,final):
    if not final or not rows or not data.get('natview_panel'):
        raise ValueError('The visual revision requires the reviewed completed evidence')
    p=Poster(out,final)
    p.rect(0,0,W,H,color='#F5F8FB')
    p.rect(*GEOMETRY['title'],color=INK,radius=13)
    p.rect(56.693,56.693,13,450,color=BLUE)
    p.para('EEG TO BOLD / COMPUTER SCIENCE PHD EXPLORATION',104,95,1590,
           size=29,color='#74D5FF',font='Body-Bold',max_h=38,role='kicker')
    for text,yy in (('Can EEG recover',153),('clinically useful fMRI?',269)):
        p.para(text,100,yy,1620,size=102,leading=112,font='Display',color='#FFFFFF',max_h=115,role='title')
    p.para(content['summary'],105,407,1570,size=34,leading=41,color='#E4F3FF',max_h=85,role='summary')
    p.hero_art()
    p.para('EXPLORATORY RESEARCH  |  MONASH M3 EXPERIMENTS  |  21 OCTOBER 2026',
           97,526,2187,size=23,color=MUTED,max_h=30,role='status')
    x,y,w,h=p.card('problem')
    p.kicker('THE CLINICAL QUESTION',x+27,y+25,w-54)
    p.heading('One task.<br/>A measurable benefit.',x+27,y+71,w-54,size=41)
    p.para(content['problem'],x+27,y+182,w-54,size=30,leading=36,max_h=112)
    p.architecture();p.scores(rows,data)
    x,y,w,h=p.card('takeaway',accent=ORANGE,fill='#FFF2DF')
    p.heading('What does a better prediction mean?',x+30,y+24,w-60,size=43)
    p.para(content['takeaway'],x+30,y+94,w-60,size=31,leading=38,max_h=116)
    p.rect(*GEOMETRY['divider'],color=ORANGE)
    p.para('THE PHD OPPORTUNITY / reliable prediction across people and sites',89,1688,W-178,
           size=47,leading=58,font='Display',color=INK,align=TA_CENTER,max_h=65,role='heading')
    p.learning(curves,data)
    x,y,w,h=p.card('methods')
    p.kicker('METHOD / TEST ON UNSEEN PEOPLE',x+27,y+22,w-54)
    p.para(content['methods'],x+27,y+70,w-54,size=30,leading=36,max_h=235)
    p.natview(data['natview_panel'])
    x,y,w,h=p.card('work_packages',accent=ORANGE)
    p.kicker('03 / THREE FALSIFIABLE THESIS QUESTIONS',x+29,y+23,w-58,color='#A55D00')
    p.heading('Recover. Transfer. Know when to stop.',x+29,y+67,w-58,size=41)
    for i,(title,body) in enumerate(content['work_packages']):
        yy=y+151+i*135
        p.circle(x+58,yy+24,31,INK)
        p.para(str(i+1),x+32,yy-1,53,size=37,font='Body-Bold',color='#FFFFFF',align=TA_CENTER,max_h=48)
        p.para(title,x+111,yy-1,w-145,size=35,font='Body-Bold',max_h=46)
        p.para(body,x+111,yy+49,w-145,size=30,leading=36,max_h=78)
        if i<2:p.line(x+111,yy+124,x+w-30,yy+124,GRID,1.5)
    x,y,w,h=p.card('models')
    p.kicker('CUTTING-EDGE MODELS / PROPOSED USES',x+29,y+23,w-58)
    yy=y+71
    for text in content['models']:
        p.para(text,x+29,yy,w-58,size=29,leading=35,max_h=72)
        yy+=59
    p.para('Healthy temporal r, different protocols: not a ranking or patient validation.',
           x+29,y+247,w-58,size=23,max_h=30,color=MUTED,role='caption')
    x,y,w,h=p.card('clinical_gate')
    p.kicker('APPLICATIONS / VALIDATION GATES',x+29,y+23,w-58)
    p.para(content['clinical_gate'],x+29,y+70,w-58,size=30,leading=37,max_h=310)
    p.line(97,3170,2285,3170,GRID,2)
    p.para(content['references'],97,3189,1660,size=23,leading=28,max_h=90,color=MUTED,role='references')
    guide_url='https://github.com/seamus-programming-stuff/NeuroBOLT/blob/main/reports/thesis_exploration/poster_reading_guide.md'
    p.para('Full explanation,<br/>methods and code',1828,3194,306,size=25,leading=30,color=MUTED,max_h=63,role='caption')
    qr=QrCodeWidget(guide_url)
    bx,by,bw,bh=qr.getBounds();side=105
    drawing=Drawing(side,side,transform=[side/(bw-bx),0,0,side/(bh-by),0,0]);drawing.add(qr)
    drawing.initialFontName='Body'
    renderPDF.draw(drawing,p.c,2175,H-3182-side)
    p.c.linkURL(guide_url,(2175,H-3182-side,2280,H-3182),relative=0,thickness=0)
    p.para('Seamus Taylor',97,3291,900,size=40,font='Display',color=BLUE,max_h=54,role='author')
    p.para('PhD thesis exploration  /  Evidence and full methods in the accompanying report',
           970,3299,1313,size=25,color=MUTED,align=TA_LEFT,max_h=35,role='author')
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
                  design_revision='v3 - explanatory methods and research narrative',
                  reference_use='A0 canvas, palette, asymmetric columns and divider; revised internal layout',
                  page_points=[W,H],geometry_points_top_origin=GEOMETRY,word_count=count,
                  content_sha256=sha(args.content),source_files=provenance,text_boxes=p.boxes,
                  input_manifest=str(args.inputs),input_manifest_sha256=sha(args.inputs) if args.inputs.exists() else None,
                  results_rows=rows,learning_rows=curves,natview_panel=data.get('natview_panel'),pdf_sha256=sha(args.out),
                  result_scope=data.get('result_scope'),protocol_caption=data.get('protocol_caption'))
    (ASSETS/'build_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'Built {args.out}\nWords: {count}; primary rows: {len(rows)}; curve rows: {len(curves)}')


if __name__=='__main__':main()
