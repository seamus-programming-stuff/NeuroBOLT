"""Render the poster's explanatory guide from its editable Markdown source."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from urllib.parse import urljoin
from xml.sax.saxutils import escape

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)
from reportlab.graphics import renderPDF
from reportlab.pdfgen.canvas import Canvas
from svglib.svglib import svg2rlg

from build_thesis_exploration_poster import fonts, INK, BLUE, ORANGE, MUTED

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'reports/thesis_exploration/poster_reading_guide.md'
OUT = ROOT / 'output/pdf/EEG_fMRI_poster_explained.pdf'
ASSETS = ROOT / 'reports/thesis_exploration/guide_figures'
BASE_URL = 'https://github.com/seamus-programming-stuff/NeuroBOLT/blob/main/reports/thesis_exploration/'
PAGE_W, PAGE_H = A4
WIDTH = PAGE_W - 84


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inline(text):
    text = escape(text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                  lambda m: f'<link color="#0075B5" href="{urljoin(BASE_URL, m[2])}">{m[1]}</link>', text)
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)


def styles():
    base = dict(fontName='Body', fontSize=10.6, leading=14.8, textColor=colors.HexColor(INK))
    return {
        'body': ParagraphStyle('body', **base, spaceAfter=9.0),
        'h1': ParagraphStyle('h1', fontName='Display', fontSize=25, leading=29,
                             textColor=colors.HexColor(INK), spaceAfter=14),
        'h2': ParagraphStyle('h2', fontName='Display', fontSize=20, leading=24,
                             textColor=colors.HexColor(INK), spaceAfter=13),
        'h3': ParagraphStyle('h3', fontName='Body-Bold', fontSize=12.2, leading=16,
                             textColor=colors.HexColor('#007BB8'), spaceBefore=3, spaceAfter=7),
        'source': ParagraphStyle('source', fontName='Body', fontSize=8.3, leading=11.4,
                                 textColor=colors.HexColor(MUTED), spaceBefore=3, spaceAfter=3),
        'bullet': ParagraphStyle('bullet', **base, leftIndent=12, firstLineIndent=-9,
                                 spaceAfter=6),
        'equation': ParagraphStyle('equation', fontName='Body-Bold', fontSize=11.5, leading=18,
                                   textColor=colors.HexColor(INK), backColor=colors.HexColor('#EAF6FF'),
                                   borderPadding=9, spaceBefore=5, spaceAfter=15),
        'table': ParagraphStyle('table', fontName='Body', fontSize=9.3, leading=12.6,
                                textColor=colors.HexColor(INK)),
        'tablehead': ParagraphStyle('tablehead', fontName='Body-Bold', fontSize=9.4, leading=12.7,
                                    textColor=colors.white),
    }


class Diagram(Flowable):
    def __init__(self, kind, width=WIDTH):
        super().__init__()
        self.kind = kind
        self.width = width
        self.height = {'physiology': 179, 'pipeline': 126, 'natview': 119, 'unebolt': 96, 'prototype': 126}[kind]

    def draw(self):
        c = self.canv
        c.saveState()
        c.scale(self.width / 511, 1)
        h = self.height

        def box(text, x, y, w, hh, fill='#EAF6FF', size=9.1):
            c.setFillColor(colors.HexColor(fill)); c.setStrokeColor(colors.HexColor('#CFDFEA'))
            c.roundRect(x, h-y-hh, w, hh, 5, fill=1, stroke=1)
            p = Paragraph(text, ParagraphStyle('node', fontName='Body', fontSize=size,
                                              leading=size*1.23, alignment=1,
                                              textColor=colors.HexColor(INK)))
            _, ph = p.wrap(w-12, hh)
            if ph > hh-8:
                raise ValueError(f'Diagram text overflow: {text}')
            p.drawOn(c, x+6, h-y-(hh+ph)/2)

        def line(x1,y1,x2,y2,color=BLUE,arrow=True):
            c.setStrokeColor(colors.HexColor(color));c.setLineWidth(1.3)
            c.line(x1,h-y1,x2,h-y2)
            if arrow:
                angle=math.atan2(y2-y1,x2-x1)
                for a in (angle-.48,angle+.48):
                    c.line(x2,h-y2,x2-6*math.cos(a),h-y2+6*math.sin(a))

        def label(text,x,y,w=511,size=8.0):
            p=Paragraph(text,ParagraphStyle('lab',fontName='Body',fontSize=size,
                                            leading=size*1.25,textColor=colors.HexColor(MUTED)))
            _,ph=p.wrap(w,100);p.drawOn(c,x,h-y-ph)

        if self.kind=='physiology':
            box('<b>Latent neural activity</b>',158,5,174,32)
            box('<b>Vascular + systemic state</b>',353,5,155,32,fill='#FFF0DA',size=8.6)
            box('<b>EEG</b><br/>Electrical scalp mixtures',5,84,196,42)
            box('<b>BOLD</b><br/>Delayed regional MRI contrast',310,84,196,42,fill='#FFF0DA')
            line(193,37,103,83);line(284,37,378,83);line(431,37,431,83,color=ORANGE)
            label('Lead fields, montage, reference',4,132,198)
            label('Haemodynamics + other influences',305,132,202)
            label('Two observations of a changing system; neither is a complete measurement of the other.',5,154,501)
        elif self.kind=='pipeline':
            nodes=[('24-s EEG history','5 groups x 5 bands'),('12 lag bins','300 log-power values'),
                   ('Fit estimator','Ridge / small MLP'),('Score BOLD','Unseen people')]
            for i,(a,b) in enumerate(nodes):
                xx=i*132;box(f'<b>{a}</b><br/>{b}',xx,10,113,45,fill='#FFF0DA' if i==3 else '#EAF6FF')
                if i<3:line(xx+114,32,xx+130,32)
            for i,(a,b) in enumerate([('Training people','Fit transforms and weights'),('Inner validation people','Choose settings / calibration'),('Outer test people','Evaluate once per person')]):
                xx=i*175;box(f'<b>{a}</b><br/>{b}',xx,77,161,40,fill='#F3F7FA',size=8.5)
        elif self.kind=='natview':
            box('<b>8 reserved people</b><br/>Pilot excluded',0,10,148,49)
            box('<b>6 eligible in v2</b><br/>2 below 60-frame gate',181,10,148,49,fill='#FFF0DA')
            box('<b>740 / 2,304 frames</b><br/>32.1% all-eight coverage',362,10,148,49,fill='#FFF0DA')
            line(149,34,180,34,color=ORANGE);line(330,34,361,34,color=ORANGE)
            label('Strict v1 accepted only 1/8. A separate metadata-only amendment preserved the model and numeric gates.',3,76,505,size=8.8)
            label('Secondary exploratory accuracy; the original eight-person confirmation was not achieved.',3,101,505)
        elif self.kind=='unebolt':
            nodes=[('16-s EEG history','Temporal + spectral'),('Shared encoder','Gated fusion'),
                   ('ROI conditioning','Embeddings + adapters'),('ROI-specific heads','Regional BOLD series')]
            for i,(a,b) in enumerate(nodes):
                xx=i*132;box(f'<b>{a}</b><br/>{b}',xx,5,113,49,fill='#FFF0DA' if i>=2 else '#EAF6FF',size=8.8)
                if i<3:line(xx+114,29,xx+130,29)
            label('Simplified UnEBOLT reference architecture; not reproduced in the current experiments.',2,69,507,size=8.3)
        elif self.kind=='prototype':
            for i,(a,b) in enumerate([('EEG + physiology','Causal acquisition'),('Quality and clocks','Preserve gaps'),('Compare models','Direct EEG / BOLD proxy'),('Advisory output','Review / insufficient signal')]):
                xx=i*132;box(f'<b>{a}</b><br/>{b}',xx,7,113,48,fill='#FFF0DA' if i==3 else '#EAF6FF',size=8.4)
                if i<3:line(xx+114,31,xx+130,31)
            box('<b>Evaluate against independent references</b><br/>Blinded labels and non-EEG corroboration',135,78,245,41,fill='#F3F7FA',size=8.6)
            line(453,56,380,98,color=ORANGE)
        c.restoreState()


class SvgFigure(Flowable):
    def __init__(self,path,width=WIDTH):
        super().__init__();self.drawing=svg2rlg(str(path))
        self.drawing.initialFontName='Body'
        self.width=width;self.factor=width/self.drawing.width
        self.height=self.drawing.height*self.factor+6

    def draw(self):
        self.canv.saveState();self.canv.scale(self.factor,self.factor)
        renderPDF.draw(self.drawing,self.canv,0,0);self.canv.restoreState()


def make_math_figure():
    ASSETS.mkdir(parents=True,exist_ok=True)
    u=np.linspace(0,2*np.pi,120,endpoint=False);y=np.sqrt(2)*np.sin(u)
    prediction=.2*y+1
    r=float(np.corrcoef(y,prediction)[0,1])
    r2=float(1-((y-prediction)**2).sum()/((y-y.mean())**2).sum())
    assert abs(r-1)<1e-12 and abs(r2+.64)<1e-12
    fig,ax=plt.subplots(figsize=(7.1,2.05))
    fig.subplots_adjust(left=.09,right=.99,bottom=.25,top=.82)
    ax.plot(np.arange(len(y)),y,color=BLUE,lw=2,label='Target: mean 0, variance 1')
    ax.plot(np.arange(len(y)),prediction,color=ORANGE,lw=2,label='Prediction: 0.2 x target + 1')
    ax.axhline(0,color='#C9D8E2',lw=.8,zorder=0)
    ax.set_xlabel('Illustrative time (not participant data)',fontsize=9)
    ax.set_ylabel('Normalized units',fontsize=9)
    ax.set_xlim(0,119);ax.set_ylim(-1.65,1.7)
    ax.tick_params(labelsize=8);ax.spines[['top','right']].set_visible(False)
    for s in ['bottom','left']:ax.spines[s].set_color('#A0B6C5')
    ax.legend(loc='upper left',bbox_to_anchor=(0,1.43),ncols=2,frameon=False,fontsize=8.3)
    path=ASSETS/'correlation_scale.svg'
    fig.savefig(path,metadata={'Date':None});plt.close(fig)
    return path,{'r':r,'predictive_R2':r2,'illustrative_only':True,'sha256':sha(path)}


def table(lines,sty):
    cells=[[s.strip() for s in line.strip().strip('|').split('|')] for line in lines]
    cells=[r for r in cells if not all(re.fullmatch(r':?-+:?',s.replace(' ','')) for s in r)]
    cols=len(cells[0])
    if cols==2:widths=[WIDTH*.29,WIDTH*.71]
    elif 'Regional r' in cells[0]:widths=[WIDTH*.51,WIDTH*.245,WIDTH*.245]
    else:widths=[WIDTH*.19,WIDTH*.40,WIDTH*.41]
    parsed=[[Paragraph(inline(s),sty['tablehead' if i==0 else 'table']) for s in row] for i,row in enumerate(cells)]
    t=Table(parsed,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor(INK)),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F1F7FB'),colors.white]),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),
        ('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#CADBE7')),
    ]))
    return t


def parse(source,sty,math_path):
    lines=source.splitlines();story=[];i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line=='<!-- page -->':story.append(PageBreak());i+=1;continue
        if line.startswith('<!-- figure:'):
            kind=line.split(':',1)[1].split('-->')[0].strip()
            story.extend([Spacer(1,3),SvgFigure(math_path) if kind=='correlation' else Diagram(kind),Spacer(1,9)])
            i+=1;continue
        if line.startswith('|'):
            group=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                group.append(lines[i]);i+=1
            story.extend([table(group,sty),Spacer(1,11)]);continue
        if line.startswith('#'):
            level=len(line)-len(line.lstrip('#'));key=f'h{min(level,3)}'
            story.append(Paragraph(inline(line[level:].strip()),sty[key]));i+=1;continue
        if line.startswith('> '):story.append(Paragraph(inline(line[2:]),sty['equation']));i+=1;continue
        if line.startswith('- '):story.append(Paragraph('- '+inline(line[2:]),sty['bullet']));i+=1;continue
        group=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(('#','<!--','|','- ','> ')):
            group.append(lines[i].strip());i+=1
        text=' '.join(group)
        key='source' if text.startswith(('Source:','Sources:','Evidence cutoff:')) else 'body'
        story.append(Paragraph(inline(text),sty[key]))
    return story


def page(canvas,doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor(BLUE));canvas.setLineWidth(3)
    canvas.line(42,PAGE_H-31,PAGE_W-42,PAGE_H-31)
    canvas.setFont('Body-Bold',8);canvas.setFillColor(colors.HexColor(MUTED))
    canvas.drawString(42,PAGE_H-23,'NEUROBOLT / POSTER EXPLANATION / EXPLORATORY RESEARCH')
    canvas.setFont('Body',8)
    canvas.drawString(42,24,'Seamus Taylor | Evidence reviewed 21 October 2026')
    canvas.drawRightString(PAGE_W-42,24,str(doc.page))
    canvas.restoreState()


def main():
    fonts();sty=styles();math_path,math_stats=make_math_figure()
    doc=BaseDocTemplate(str(OUT),pagesize=A4,leftMargin=42,rightMargin=42,
                        topMargin=49,bottomMargin=42,title='EEG to fMRI: what the poster means',
                        author='Seamus Taylor')
    doc.addPageTemplates([PageTemplate(id='guide',frames=[Frame(42,42,WIDTH,PAGE_H-91,
                            leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=page)])
    source=SOURCE.read_text(encoding='utf-8')
    def canvasmaker(*args,**kwargs):
        kwargs['initialFontName']='Body'
        return Canvas(*args,**kwargs)
    doc.build(parse(source,sty,math_path),canvasmaker=canvasmaker)
    manifest={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':sha(SOURCE),
              'pdf':str(OUT.relative_to(ROOT)),'pdf_sha256':sha(OUT),
              'planned_sections':9,'evidence_report_sha256':sha(ROOT/'reports/Clinical EEG fMRI thesis exploration.md'),
              'math_figure':math_stats,'source_word_count':len(re.findall(r'\b[\w\'-]+\b',source)),
              'revision_role':'Explanatory synthesis of reviewed results; no new experiment',
              'reference_designs':['example1: background/method/evaluation/further research narrative',
                                   'example2: explanatory pipeline and asymmetric cyan/orange composition']}
    (ASSETS/'build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'Built {OUT}; source words: {manifest["source_word_count"]}')


if __name__=='__main__':
    main()
