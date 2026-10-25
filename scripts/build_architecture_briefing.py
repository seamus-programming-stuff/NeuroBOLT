"""Build a readable NeuroBOLT research-directions PDF from reviewed Markdown.

This is a document renderer. It never trains models or submits cluster jobs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from urllib.parse import urljoin
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)
from reportlab.pdfgen.canvas import Canvas

from build_thesis_exploration_poster import fonts

ROOT = Path(__file__).resolve().parents[1]
PAGE_W, PAGE_H = A4
WIDTH = PAGE_W - 88
INK, BLUE, ORANGE = '#153044', '#007BB8', '#D97924'
MUTED, PALE, WARM = '#4E6575', '#EAF4FA', '#FFF0DF'
BASE_URL = 'https://github.com/seamus-programming-stuff/NeuroBOLT/blob/neurobolt/reports/'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inline(text):
    # Only simple Markdown is accepted. All text is escaped before PDF markup.
    text = text.replace('—', ' - ').replace('–', '-').replace('\u2011', '-')
    text = text.replace('10⁻⁶', '10^(-6)').replace('10⁻⁴', '10^(-4)')
    text = escape(text)
    def link(match):
        address=match[2]
        if address.startswith('&lt;') and address.endswith('&gt;'):
            address=address[4:-4]
        return '<link color="' + BLUE + '" href="' + urljoin(BASE_URL,address) + '">' + match[1] + '</link>'
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', text)
    return re.sub(r'`([^`]+)`', r'<font name="Body">\1</font>', text)


def styles():
    common = dict(fontName='Body', fontSize=10.4, leading=14.5, textColor=colors.HexColor(INK))
    return {
        'body': ParagraphStyle('body', **common, spaceAfter=8.2),
        'h1': ParagraphStyle('h1', fontName='Display', fontSize=26, leading=31,
                             textColor=colors.HexColor(INK), spaceAfter=15, keepWithNext=True),
        'h2': ParagraphStyle('h2', fontName='Display', fontSize=18.5, leading=23,
                             textColor=colors.HexColor(INK), spaceBefore=9, spaceAfter=11, keepWithNext=True),
        'h3': ParagraphStyle('h3', fontName='Body-Bold', fontSize=12, leading=16,
                             textColor=colors.HexColor(BLUE), spaceBefore=6, spaceAfter=7, keepWithNext=True),
        'bullet': ParagraphStyle('bullet', **common, leftIndent=11, firstLineIndent=-9, spaceAfter=6),
        'small': ParagraphStyle('small', fontName='Body', fontSize=8.3, leading=11.5,
                                textColor=colors.HexColor(MUTED), spaceAfter=6),
        'reference': ParagraphStyle('reference', fontName='Body', fontSize=8.4, leading=11.3,
                                    textColor=colors.HexColor(MUTED), leftIndent=8,
                                    firstLineIndent=-7, spaceAfter=3),
        'equation': ParagraphStyle('equation', fontName='Body', fontSize=10.1, leading=15,
                                   textColor=colors.HexColor(INK), backColor=colors.HexColor(PALE),
                                   borderPadding=9, spaceBefore=5, spaceAfter=13),
        'table': ParagraphStyle('table', fontName='Body', fontSize=8.7, leading=11.6,
                               textColor=colors.HexColor(INK)),
        'tablehead': ParagraphStyle('tablehead', fontName='Body-Bold', fontSize=8.8,
                                   leading=11.8, textColor=colors.white),
    }


class ResearchDiagram(Flowable):
    """Schematic vectors, not generated images or participant recordings."""
    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        self.width = WIDTH
        self.height = {'neurobolt': 202, 'lag': 153, 'data': 156,
                       'evaluation': 132, 'directions': 156, 'results': 143,
                       'alignment': 192, 'pilot': 172}[kind]

    def draw(self):
        c = self.canv
        c.saveState()
        c.scale(self.width / 507, 1)
        h = self.height

        def box(label, x, y, w, hh, fill=PALE, size=8.9):
            c.setFillColor(colors.HexColor(fill))
            c.setStrokeColor(colors.HexColor('#CFDFE9'))
            c.roundRect(x, h-y-hh, w, hh, 5, fill=1, stroke=1)
            p = Paragraph(label, ParagraphStyle('node', fontName='Body', fontSize=size,
                           leading=size*1.2, alignment=1, textColor=colors.HexColor(INK)))
            _, ph = p.wrap(w-12, hh)
            if ph > hh-8:
                raise ValueError('Diagram label does not fit: ' + label)
            p.drawOn(c, x+6, h-y-(hh+ph)/2)

        def line(x1,y1,x2,y2,color=BLUE,arrow=True,dashed=False):
            c.setStrokeColor(colors.HexColor(color)); c.setLineWidth(1.2)
            c.setDash(3,2) if dashed else c.setDash()
            c.line(x1,h-y1,x2,h-y2)
            c.setDash()
            if arrow:
                angle=math.atan2(y2-y1,x2-x1)
                for a in (angle-.45,angle+.45):
                    c.line(x2,h-y2,x2-5*math.cos(a),h-y2+5*math.sin(a))

        def label(text,x,y,w=507,size=8):
            p=Paragraph(text,ParagraphStyle('lab',fontName='Body',fontSize=size,
                        leading=size*1.25,textColor=colors.HexColor(MUTED)))
            _,ph=p.wrap(w,100)
            p.drawOn(c,x,h-y-ph)

        if self.kind == 'neurobolt':
            box('<b>Past EEG window</b><br/>Channels x time samples',0,68,118,49)
            box('<b>Temporal / spatial branch</b><br/>LaBraM token encoder',153,11,186,49)
            box('<b>Spectral branch</b><br/>Multiscale spectral representation',153,125,186,49)
            box('<b>Mean-pool each branch</b><br/>Add + GELU + linear head',372,68,132,49,fill=WARM,size=8.3)
            line(118,80,151,35);line(118,105,151,149)
            line(340,35,371,80);line(340,149,371,105)
            line(438,118,438,132,color=ORANGE)
            label('Regional BOLD at frame t<br/>[batch, regions]',372,136,132,size=8.2)
            label('Conceptual branch structure. The text explains the implementation, tensor shapes and measured branch ablations.',2,181,501)
        elif self.kind == 'lag':
            nodes=[('EEG history','Fixed time bins'),('Lag tokens','Spectral values + position'),
                   ('Small encoder','Temporal mixing'),('Readout','Mean / learned weights')]
            for i,(a,b) in enumerate(nodes):
                xx=i*129;box(f'<b>{a}</b><br/>{b}',xx,8,118,52,fill=WARM if i==3 else PALE,size=8.2)
                if i<3:line(xx+119,34,xx+128,34)
            box('<b>Compare with measured BOLD</b><br/>Same rows, preprocessing, loss and evaluation across estimators',0,89,505,42,fill='#F4F7FA')
            line(446,61,446,88,color=ORANGE)
            label('Proposed compact pilot. It is not a full NeuroBOLT replacement or an independently confirmed improvement.',2,138,501,size=7.8)
        elif self.kind == 'alignment':
            box('<b>24 s EEG history</b><br/>STFT supports: 0.5, 1, 2 and 4 s',0,7,146,54,size=8.4)
            box('<b>Current window maps</b><br/>Learned dense mixing of time positions',177,7,151,54,size=8.4)
            box('<b>Proposed window maps</b><br/>Fixed weights from physical overlap',354,7,151,54,fill=WARM,size=8.4)
            line(147,29,176,29)
            line(328,34,353,34,color=ORANGE)
            label('One component is replaced',329,68,176,size=7.7)
            # A common, physical-time grid; blocks illustrate STFT support only.
            label('Same output grid: 48 half-second bins over the previous 24 seconds',0,83,506,size=8.5)
            for i in range(48):
                c.setFillColor(colors.HexColor('#D9EAF4' if i%2==0 else '#EDF5FA'))
                c.setStrokeColor(colors.white)
                c.rect(i*10.5,h-119,10.5,14,fill=1,stroke=1)
            label('Older EEG',0,124,140,size=7.5)
            label('BOLD frame t',437,124,70,size=7.5)
            box('Keep spectral magnitudes, frequency projections, scale sum, encoder and mean readout fixed.',0,146,505,34,fill='#F4F7FA',size=8.4)
        elif self.kind == 'data':
            box('<b>Paired EEG + fMRI</b><br/>Fit and evaluate EEG-to-BOLD',0,10,242,53)
            box('<b>EEG-only recordings</b><br/>Representation / robustness studies',264,10,242,53,fill=WARM)
            box('<b>VU, ds006040, NATVIEW</b><br/>Check targets, clocks, splits and QC',0,88,242,51)
            box('<b>Prospective Emotiv / Monash</b><br/>Confirm task, montage, licence and access',264,88,242,51,fill=WARM)
            line(121,64,121,87);line(385,64,385,87,color=ORANGE)
        elif self.kind == 'evaluation':
            for i,(a,b) in enumerate([('Training people','Fit transforms + weights'),('Validation people','Choose settings / epoch'),('Held-out people','Report all outcomes')]):
                xx=i*173;box(f'<b>{a}</b><br/>{b}',xx,10,160,53,size=8.5)
                if i<2:line(xx+161,36,xx+171,36)
            box('All recordings and overlapping windows from the same person stay together.',0,83,505,33,fill=WARM,size=8.8)
        elif self.kind == 'directions':
            for i,(a,b) in enumerate([('Temporal structure','Lag-aware tokens / HRF prior'),('Regional structure','ROI-conditioned readout'),('Transfer and measurement','Montage-aware pretraining / QC')]):
                xx=i*173;box(f'<b>{a}</b><br/>{b}',xx,9,160,61,fill=WARM if i==2 else PALE,size=8.4)
            box('<b>Shared decision rule</b><br/>A new component earns its complexity through a matched baseline and a falsifiable test.',0,96,505,43,fill='#F4F7FA',size=8.8)
        elif self.kind == 'results':
            # Values transcribed from the fixed original five-fold subject CV.
            values=[('Ridge, fine bins, 24 s',.381,.306,.456),
                    ('NeuroBOLT shared, 24 s',.336,.266,.405),
                    ('NeuroBOLT shared, 16 s',.323,.255,.390)]
            x0,xw=222,250
            for i,(name,mean,low,high) in enumerate(values):
                y=25+i*31
                label(name,0,y-7,210,size=9)
                xx=lambda v:x0+v/.55*xw
                c.setStrokeColor(colors.HexColor(ORANGE if i==0 else BLUE));c.setLineWidth(2)
                c.line(xx(low),h-y,xx(high),h-y)
                c.setFillColor(colors.HexColor(ORANGE if i==0 else BLUE));c.circle(xx(mean),h-y,3.5,fill=1,stroke=0)
                label(f'{mean:.3f}',477,y-6,30,size=8)
            label('Original VU study: mean over 22 people, seven targets; lines show reported 95% confidence intervals.',0,115,505,size=7.8)
        elif self.kind == 'pilot':
            run = ROOT/'reports/architecture_briefing/pilot/20261026_ec_global_v1/summary_verified.json'
            summary = json.loads(run.read_text(encoding='utf-8'))
            x0, xw = 221, 256
            xx = lambda value: x0 + (value + .12) / .24 * xw
            line(xx(0),8,xx(0),127,color='#9AACB7',arrow=False,dashed=True)
            for i,(name,key) in enumerate([('Ridge','ridge'),('MLP','mlp32'),('Transformer / mean','transformer_mean'),('Transformer / learned pool','transformer_lag')]):
                metric=summary['models'][key]['predictive_R2']
                low,high=metric['ci95'];mean=metric['mean'];y=22+i*28
                label(name,0,y-6,210,size=9)
                col=ORANGE if key=='ridge' else (MUTED if key=='mlp32' else BLUE)
                line(xx(low),y,xx(high),y,color=col,arrow=False)
                c.setFillColor(colors.HexColor(col));c.circle(xx(mean),h-y,3.4,fill=1,stroke=0)
            line(xx(-.10),127,xx(.10),127,color=MUTED,arrow=False)
            for value in [-.1,0,.1]:
                line(xx(value),127,xx(value),131,color=MUTED,arrow=False)
                label(f'{value:+.2f}',xx(value)-12,134,38,size=7.5)
            label('Raw predictive R²; dotted line = run-mean reference; intervals = person-bootstrap 95%.',0,157,505,size=7.8)
        c.restoreState()


def make_table(lines, sty):
    rows=[[cell.strip() for cell in line.strip().strip('|').split('|')] for line in lines]
    rows=[row for row in rows if not all(re.fullmatch(r':?-+:?',cell.replace(' ','')) for cell in row)]
    columns=len(rows[0])
    if not all(len(row)==columns for row in rows):
        raise ValueError('Unequal Markdown table column count')
    ratios={2:[.30,.70],3:[.22,.39,.39],4:[.18,.29,.27,.26],5:[.16,.21,.21,.21,.21]}.get(columns)
    if ratios is None:
        raise ValueError('Use at most five table columns in a reading document')
    values=[[Paragraph(inline(cell),sty['tablehead' if index==0 else 'table'])
             for cell in row] for index,row in enumerate(rows)]
    result=Table(values,colWidths=[WIDTH*r for r in ratios],repeatRows=1,hAlign='LEFT')
    result.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor(INK)),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F0F6FA'),colors.white]),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),
        ('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#CBDCE6')),
    ]))
    return result


def parse(source, sty):
    lines=source.splitlines();story=[];i=0;references=False
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line=='<!-- page -->':story.append(PageBreak());i+=1;continue
        if line.startswith('<!-- figure:'):
            kind=line.split(':',1)[1].split('-->')[0].strip()
            story.extend([ResearchDiagram(kind),Spacer(1,10)]);i+=1;continue
        if line.startswith('<!--'):i+=1;continue
        if line.startswith('|'):
            group=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                group.append(lines[i]);i+=1
            story.extend([make_table(group,sty),Spacer(1,10)]);continue
        if line.startswith('#'):
            level=len(line)-len(line.lstrip('#'))
            references = 'Selected primary references' in line
            story.append(Paragraph(inline(line[level:].strip()),sty[f'h{min(level,3)}']))
            i+=1;continue
        if line.startswith('> '):
            story.append(Paragraph(inline(line[2:]),sty['equation']));i+=1;continue
        if line.startswith('- '):
            story.append(Paragraph('- '+inline(line[2:]),sty['reference' if references else 'bullet']));i+=1;continue
        if re.match(r'^\d+\. ',line):
            story.append(Paragraph(inline(line),sty['bullet']));i+=1;continue
        group=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(('#','<!--','|','- ','> ')) and not re.match(r'^\d+\. ',lines[i].strip()):
            group.append(lines[i].strip());i+=1
        text=' '.join(group)
        key='small' if text.startswith(('Source:','Sources:','Evidence cutoff:','Reading note:','Status:')) else 'body'
        story.append(Paragraph(inline(text),sty[key]))
    return story


def page(canvas,doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor(BLUE));canvas.setLineWidth(3)
    canvas.line(44,PAGE_H-31,PAGE_W-44,PAGE_H-31)
    canvas.setFont('Body-Bold',7.6);canvas.setFillColor(colors.HexColor(MUTED))
    canvas.drawString(44,PAGE_H-23,'NEUROBOLT / ARCHITECTURE AND RESEARCH DIRECTIONS')
    canvas.setFont('Body',8)
    canvas.drawString(44,24,'Evidence review: 26 October 2026 | Exploratory research')
    canvas.drawRightString(PAGE_W-44,24,str(doc.page))
    canvas.restoreState()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=ROOT/'reports/NeuroBOLT architecture research briefing.md')
    parser.add_argument('--out',type=Path,default=ROOT/'output/pdf/NeuroBOLT_architecture_research_briefing.pdf')
    args=parser.parse_args()
    fonts();args.out.parent.mkdir(parents=True,exist_ok=True)
    source=args.source.read_text(encoding='utf-8')
    doc=BaseDocTemplate(str(args.out),pagesize=A4,leftMargin=44,rightMargin=44,
                        topMargin=48,bottomMargin=42,title='NeuroBOLT: architecture and research directions',author='Seamus Taylor')
    doc.addPageTemplates([PageTemplate(id='reading',frames=[Frame(44,42,WIDTH,PAGE_H-91,
                           leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=page)])
    def canvasmaker(*a,**kw):
        kw['initialFontName']='Body'
        return Canvas(*a,**kw)
    doc.build(parse(source,styles()),canvasmaker=canvasmaker)
    manifest={'source':str(args.source.relative_to(ROOT)), 'source_sha256':sha(args.source),
              'pdf':str(args.out.relative_to(ROOT)), 'pdf_sha256':sha(args.out),
              'renderer_sha256':sha(Path(__file__)),
              'word_count':len(re.findall(r"\b[\w'-]+\b",source)),
              'figure_kinds':re.findall(r'<!-- figure:\s*(\w+)\s*-->',source),
              'role':'Research synthesis. New pilot evidence, if included, must identify its own protocol and limitations.'}
    if '<!-- figure: pilot -->' in source:
        pilot = ROOT/'reports/architecture_briefing/pilot/20261026_ec_global_v1/summary_verified.json'
        manifest['pilot_summary'] = pilot.relative_to(ROOT).as_posix()
        manifest['pilot_summary_sha256'] = sha(pilot)
    (ROOT/'reports/architecture_briefing/build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':
    main()
