"""Build the illustrated, stakeholder-facing clinical feasibility research brief.

Source: reports/Clinical EEG to fMRI feasibility.md (evidence audit, 21 Oct 2026).
The diagrams are vector schematics, not simulated or observed patient results.
"""
from pathlib import Path
import math
import re
from html import escape

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether, Flowable,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf/Clinical_EEG_to_fMRI_feasibility.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)
for name, fname in (("Arial", "arial.ttf"), ("Arial-Bold", "arialbd.ttf"),
                    ("Arial-Italic", "ariali.ttf"), ("Arial-BoldItalic", "arialbi.ttf")):
    pdfmetrics.registerFont(TTFont(name, str(Path("C:/Windows/Fonts") / fname)))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold",
                            italic="Arial-Italic", boldItalic="Arial-BoldItalic")

NAVY = colors.HexColor("#142F47")
TEAL = colors.HexColor("#007F82")
BLUE = colors.HexColor("#3B6FA0")
INK = colors.HexColor("#233442")
MUTED = colors.HexColor("#566878")
LINE = colors.HexColor("#D9E3EA")
PALE = colors.HexColor("#EDF5F7")
ORANGE = colors.HexColor("#AB5E21")
CREAM = colors.HexColor("#FBF3E8")
W, H = 595.276, 841.89
M = 43
CW = W - 2*M
ST = {
    "title": ParagraphStyle("title", fontName="Arial-Bold", fontSize=25, leading=28, textColor=NAVY, spaceAfter=11),
    "h1": ParagraphStyle("h1", fontName="Arial-Bold", fontSize=20, leading=23, textColor=NAVY, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="Arial-Bold", fontSize=12.4, leading=15.5, textColor=NAVY, spaceBefore=9, spaceAfter=5),
    "body": ParagraphStyle("body", fontName="Arial", fontSize=10.25, leading=14.1, textColor=INK, spaceAfter=8),
    "summary": ParagraphStyle("summary", fontName="Arial", fontSize=11.2, leading=15.6, textColor=NAVY, spaceAfter=12),
    "small": ParagraphStyle("small", fontName="Arial", fontSize=9.8, leading=13.3, textColor=INK, spaceAfter=7),
    "caption": ParagraphStyle("caption", fontName="Arial", fontSize=8.4, leading=11, textColor=MUTED, spaceAfter=8),
    "table": ParagraphStyle("table", fontName="Arial", fontSize=9.3, leading=12.6, textColor=INK),
    "th": ParagraphStyle("th", fontName="Arial-Bold", fontSize=9, leading=12, textColor=colors.white),
    "ref": ParagraphStyle("ref", fontName="Arial", fontSize=8.4, leading=11.3, textColor=INK, spaceAfter=5),
    "eyebrow": ParagraphStyle("eyebrow", fontName="Arial-Bold", fontSize=8.4, leading=11, textColor=TEAL, spaceAfter=8),
}

REFS = []
REF_MAP = {}
def norm(s):
    return s.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", " - ").replace("\u2212", "-").replace("\u00a0", " ")

def cite(title, url):
    if url not in REF_MAP:
        REF_MAP[url] = len(REFS)+1
        REFS.append((title, url))
    n = REF_MAP[url]
    return f' <super><a href="{escape(url, quote=True)}" color="#007F82">[{n}]</a></super>'

def P(s, style="body"):
    return Paragraph(norm(s), ST[style])

story = []
def add(s, style="body"):
    story.append(P(s, style))

def section(number, title):
    if story:
        story.append(PageBreak())
    add(f"RESEARCH BRIEF  /  {number}", "eyebrow")
    add(title, "h1")

def sub(title):
    add(title, "h2")

def callout(title, body, tint=PALE):
    t=Table([[P(title, "h2")], [P(body, "small")]], colWidths=[CW-20])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),tint), ("BOX",(0,0),(-1,-1),0.5,LINE),
                           ("LEFTPADDING",(0,0),(-1,-1),10), ("RIGHTPADDING",(0,0),(-1,-1),10),
                           ("TOPPADDING",(0,0),(-1,0),1), ("BOTTOMPADDING",(0,-1),(-1,-1),7)]))
    story.extend([KeepTogether(t), Spacer(1,9)])

def table(headers, rows, widths):
    data=[[P(x,"th") for x in headers]] + [[P(x,"table") for x in row] for row in rows]
    t=Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),NAVY), ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),8), ("RIGHTPADDING",(0,0),(-1,-1),8),
        ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,PALE]),
        ("LINEBELOW",(0,0),(-1,0),0.6,NAVY), ("LINEBELOW",(0,1),(-1,-1),0.4,LINE),
    ]))
    story.extend([t, Spacer(1,9)])

class Diagram(Flowable):
    def __init__(self, kind, height):
        Flowable.__init__(self)
        self.kind, self.width, self.height = kind, CW, height

    def draw(self):
        c=self.canv
        getattr(self, self.kind)(c)

    def label(self,c,txt,x,y,w,sz=9,bold=False,color=INK,leading=None):
        st=ParagraphStyle("d",fontName="Arial-Bold" if bold else "Arial",fontSize=sz,
                          leading=leading or sz*1.28,textColor=color)
        p=Paragraph(norm(txt),st)
        _,ph=p.wrap(w,1000)
        p.drawOn(c,x,y-ph)
        return ph

    def box(self,c,x,y,w,h,title,body,fill=PALE,accent=TEAL):
        c.setFillColor(fill);c.setStrokeColor(LINE)
        c.roundRect(x,y,w,h,6,fill=1,stroke=1)
        c.setFillColor(accent);c.roundRect(x,y+h-4,w,4,2,fill=1,stroke=0)
        th=self.label(c,title,x+10,y+h-12,w-20,10,True,NAVY)
        self.label(c,body,x+10,y+h-19-th,w-20,8.8)

    def arrow(self,c,x1,y1,x2,y2,color=TEAL,dash=False):
        c.setStrokeColor(color);c.setLineWidth(1.25)
        if dash:c.setDash(3,2)
        c.line(x1,y1,x2,y2);c.setDash()
        a=math.atan2(y2-y1,x2-x1)
        p=c.beginPath();p.moveTo(x2,y2)
        p.lineTo(x2-6*math.cos(a-.45),y2-6*math.sin(a-.45))
        p.lineTo(x2-6*math.cos(a+.45),y2-6*math.sin(a+.45));p.close()
        c.setFillColor(color);c.drawPath(p,fill=1,stroke=0)

    def pipeline(self,c):
        self.box(c,0,131,147,73,"Scalp EEG","Mixed electrical activity<br/>Finite channels + noise")
        self.box(c,181,131,147,73,"Prediction model","EEG history → estimated<br/>regional BOLD time course")
        self.box(c,362,131,147,73,"Measured fMRI","Neural + vascular response<br/>Systemic physiology + noise")
        self.arrow(c,147,168,181,168)
        self.arrow(c,328,168,362,168,BLUE,True)
        self.label(c,"test",333,186,28,7,color=BLUE)
        self.box(c,0,19,236,77,"What better learning can change","Features, history, fit, personal calibration<br/>and transfer to new people/sites")
        self.box(c,273,19,236,77,"What new measurements can change","Respiration / CO2, anatomy, denser EEG,<br/>vascular calibration and sensor quality",CREAM,ORANGE)
        self.arrow(c,118,96,218,131,TEAL,True)
        self.arrow(c,390,96,438,131,ORANGE,True)

    def metrics(self,c):
        gap=12; bw=(CW-2*gap)/3
        for i,title in enumerate(["Temporal correlation", "Spatial similarity", "Connectivity similarity"]):
            x=i*(bw+gap)
            c.setFillColor(PALE);c.roundRect(x,1,bw,190,6,fill=1,stroke=0)
            self.label(c,title,x+10,179,bw-20,10,True,NAVY)
        # Time-aligned schematic, two traces with phase mismatch, not empirical data.
        x0=12; y0=91; ww=bw-24
        c.setStrokeColor(LINE);c.line(x0,y0-13,x0+ww,y0-13)
        c.line(x0,y0-13,x0,y0+33)
        for phase,co in [(0,TEAL),(.95,ORANGE)]:
            p=c.beginPath()
            for j in range(70):
                x=x0+j*ww/69; y=y0+12+16*math.sin(j*.15+phase)
                (p.moveTo if j==0 else p.lineTo)(x,y)
            c.setStrokeColor(co);c.setLineWidth(1.7);c.drawPath(p)
        self.label(c,"Do the same region's rises and falls align in time?",10,64,bw-20,9)
        # Spatial schematic uses arbitrary colour chips explicitly identified below.
        bx=bw+gap+20
        for row in range(2):
            for j in range(6):
                f=[.2,.6,.9,.4,.7,.15][j]+(.05 if row else 0)
                c.setFillColor(colors.Color(1-f*.8,1-f*.4,1-f*.2))
                c.roundRect(bx+j*20,98-row*25,17,20,2,fill=1,stroke=0)
        self.label(c,"Does one brain pattern resemble the measured pattern?",bw+gap+10,64,bw-20,9)
        # Connectivity: identical structure after common time permutation.
        bx=2*(bw+gap)+20
        for rr in range(5):
            for cc in range(5):
                f=1-abs(rr-cc)/5
                c.setFillColor(colors.Color(1-f*.75,1-f*.38,1-f*.2))
                c.rect(bx+cc*14,83+rr*10,12,8,fill=1,stroke=0)
        self.label(c,"Do relationships between regional traces resemble each other?",2*(bw+gap)+10,64,bw-20,9)

    def errors(self,c):
        self.box(c,0,57,237,119,"1  Remaining uncertainty given X",
                 "Different actual BOLD values can remain compatible with the same observed inputs.<br/><br/>Add informative sensors or calibration to change X.",CREAM,ORANGE)
        self.box(c,272,57,237,119,"2  Model / estimation error",
                 "The fitted model can miss the best prediction supported by those inputs.<br/><br/>Improve features, training data, fitting and transfer.")
        self.label(c,"+",246,127,20,22,True,NAVY)
        self.label(c,"Total expected squared error = term 1 + term 2",0,38,CW,11,True,NAVY)
        self.label(c,"A large observed residual does not identify which term dominates.",0,18,CW,9,color=MUTED)

    def gates(self,c):
        labels=[("Define one action","Target + comparator"),("External technical test","Frozen model; new sites"),
                ("Silent prospective use","Timing + failures"),("Clinical utility study","Benefit + harms")]
        bw=(CW-3*12)/4
        for i,(title,body) in enumerate(labels):
            x=i*(bw+12)
            self.box(c,x,32,bw,88,title,body)
            if i<3:self.arrow(c,x+bw,76,x+bw+12,76)
        self.label(c,"Gate at every step: meet prespecified limits, narrow the claim, or change the measurement.",0,18,CW,9,color=MUTED)

    def study(self,c):
        self.box(c,0,100,148,101,"Input information","EEG only<br/>Physiology only<br/>EEG + physiology<br/>Personal calibration")
        self.box(c,180,100,148,101,"Learning resources","Training people<br/>Minutes per person<br/>Ridge / kernel / neural<br/>Nested tuning")
        self.box(c,360,100,149,101,"Fixed evaluation","New people and sites<br/>Real regional BOLD<br/>Independent arousal labels<br/>Causal preprocessing")
        self.arrow(c,148,150,180,150);self.arrow(c,328,150,360,150)
        self.label(c,"Compare the same held-out cases",0,77,CW,11,True,NAVY)
        self.label(c,"Temporal r • calibrated R² • amplitude and lag • regional residuals • failures / abstentions",0,54,CW,9)
        self.label(c,"Sensor gain → improve acquisition. Reliable nonlinear gain → increase model capacity. Neither → revise the target.",0,27,CW,9,color=MUTED)


# 1. Opening summary appears immediately below the title, without a cover page.
add("EVIDENCE REVIEW  /  21 OCTOBER 2026", "eyebrow")
add("Can EEG become<br/>clinically useful fMRI?", "title")
add("EEG predicts some real fMRI BOLD fluctuations, but reliable patient-specific whole-brain replacement has not been demonstrated. Recent models report regional temporal correlations around 0.37-0.43 under different protocols; much higher spatial scores answer a different question. Missing spatial and vascular information, noisy measurements and weak patient/site validation remain unresolved barriers. A narrow arousal advisory or regional-feedback application is the practical next step. Study hundreds of paired participants with compact models, then validate a frozen system prospectively. Those cohort sizes are planning proposals, not proven clinical thresholds; no defensible dataset or model size guarantees broad fMRI replacement.", "summary")
add("An illustrated briefing for an advisor and a small research team", "caption")
story.append(Diagram("pipeline",215))
add("Figure 1. The prediction is an estimate of a haemodynamic measurement. Better learning and additional measurements address different parts of the problem. Conceptual schematic; no patient data shown.","caption")
sub("What the team should take away")
add("<b>Capability:</b> genuine prediction and promising clinical surrogates exist. <b>Limit:</b> plausible images, regional correlations and patient-specific clinical decisions are separate achievements. <b>Investment:</b> test information value and a defined clinical action before collecting a large replacement-imaging cohort.")
add("This brief condenses the project's full evidence audit. Published results, internal exploratory findings and hypothetical resource calculations are explicitly separated. It includes no newly run model experiments.","small")

# 2. Metrics.
section("01", "Understand what an accuracy score means")
add("BOLD means blood-oxygen-level-dependent signal: fMRI tracks a delayed haemodynamic response, rather than directly recording electrical firing. An EEG-to-fMRI model can be evaluated along several different axes.")
story.append(Diagram("metrics",199))
add("Figure 2. Three distinct questions. Traces, colour strips and matrix are illustrative. Their values are not research results.","caption")
add("A common time permutation applied to every regional trace preserves functional connectivity while destroying alignment with measured events. Consequently, high connectivity similarity alone cannot show recovery of the original timeline.")
add("<b>Metric glossary:</b> r/R = Pearson correlation; MSE = mean squared error (lower is better); SSIM = structural image similarity; CCC = concordance, which also penalizes mismatched mean and scale; FC = functional connectivity. Each still needs its axis and aggregation specified.","small")
table(["Matched comparison in one paper", "Temporal result", "What it establishes"], [
    ["MARBLE: 64 atlas regions", "R 0.434 ± 0.047\nvs NeuroBOLT 0.406 ± 0.038", "Improvement under that paper's matched protocol; no external patient validation."],
    ["UniEFS: 512 atlas regions", "R 0.367 ± 0.052\nvs NeuroBOLT 0.331 ± 0.044", "Broader regional prediction; its primary test is not an unseen acquisition site."],
    ["Qu et al.: within-person videos", "Spatial r 0.824", "Substantial spatial reconstruction after extensive personal paired training; different endpoint."],
], [165,155,CW-320])
add("The 0.473 reported for NeuroBOLT's seven selected targets cannot be ranked against MARBLE's 64-region 0.434 or UniEFS's 512-region 0.367. Region coverage, participants, calibration and aggregation differ. In the tables here, ± denotes the paper's reported standard deviation, not a confidence interval.","small")
callout("Ask this before repeating a headline score", "What is correlated, over which axis, in how many independent people, with how much personal calibration, and on which genuinely new site? Was the comparator retrained using the same protocol?")

# 3. Main model audit.
section("02", "What the leading temporal models show")
add("These are reported paper results, not new reproductions. The small VU dataset recurs across methods, so several papers do not amount to several independent clinical cohorts.","small")

def model(title, body):
    story.append(KeepTogether([P(title,"h2"),P(body,"small")]))

model("NeuroBOLT | NeurIPS 2024", "<b>Test:</b> VU, 22 healthy people / 29 scans, one site; 18/5/6 train/validation/test scans grouped by person. Six selected regions plus global BOLD; 16 s EEG history. <b>Temporal R:</b> 0.473 across unseen-person targets; 0.531 within scan. Code, data and weights are public. The original main benchmark lacks matched ridge; split-file provenance merits audit." + cite("NeuroBOLT: paper and original temporal results", "https://arxiv.org/html/2410.05341v2"))
model("UnEBOLT | MIDL 2026", "<b>Test:</b> same VU cohort/site; six held-out scans from five people. <b>Temporal R:</b> 0.418 ± 0.036 at 64 regions; 0.386 / 0.360 at 128 / 256. Its FC-edge R of 0.549 ± 0.120 is a separate endpoint. Approximately <b>8.2 million parameters</b>. Code is available; trained weights were not verified." + cite("UnEBOLT: MIDL 2026 full paper", "https://raw.githubusercontent.com/mlresearch/v315/main/assets/li26g/li26g.pdf"))
model("MARBLE | MICCAI 2026", "<b>Test:</b> same 22 people / 29 scans, subject-wise split, six test scans; unique test-person count unresolved in the audit. <b>64-region temporal R:</b> 0.434 ± 0.047; MSE 0.210 ± 0.020. Matched UnEBOLT is 0.412 and NeuroBOLT 0.406. Only <b>2.6 million parameters</b>. Code exists; checkpoints were pending in the inspected README. No external cohort or formal significance test." + cite("MARBLE: MICCAI 2026 full paper", "https://papers.miccai.org/miccai-2026/paper/4437_paper.pdf"))
model("UniEFS / Mind the State | ICML 2026", "<b>Training:</b> unpaired fMRI pretraining on 375 HCP people / 1,500 scans; paired training on 18 VU and 10 NIH scans, with five validation and six subject-disjoint test scans. Unique paired-person total unresolved. <b>512-region temporal R:</b> 0.367 ± 0.052; cortex 0.394, subcortex 0.276, cerebellum 0.247. Uses demographic, dataset and vigilance context. Main test remains VU. Code/data were coming soon; weights unverified. Epoch-derived vigilance prompts require an online causality audit." + cite("UniEFS / Mind the State: ICML 2026 full paper", "https://raw.githubusercontent.com/mlresearch/v306/main/assets/li26gp/li26gp.pdf"))
callout("Positive progress, still a narrow evidence base", "MARBLE and UniEFS improve their own matched temporal comparisons. Neither paper demonstrates a clinically sufficient effect. Unpaired fMRI pretraining can strengthen a decoder prior; it does not itself validate patient-specific information carried by EEG.")
add("There is limited positive transfer evidence: NeuroBOLT reports frozen external auditory-task R 0.380 vs 0.373 trained there. That dataset has ten people / 16 scans, with four test scans. Similar point estimates do not establish equivalence. UniEFS also reports leave-one-dataset-out analyses; its primary 0.367 is not an unseen-site result.","small")

# 4. Other evidence.
section("03", "Promising results that need careful qualification")
model("MEL | August 2026 preprint", "VU 22 people / 29 scans; claims leave-one-subject-out testing. Seven-target temporal means: ridge 0.439, MLP 0.488, ensemble 0.499. However, the NeuroBOLT comparator exactly repeats original fixed-split numbers despite claimed matched LOSO reruns. That provenance discrepancy is unresolved. Code and weights not located." + cite("MEL: preprint, August 2026", "https://arxiv.org/html/2608.29304v1"))
model("CATD | IEEE TMI 2025", "XP1: 10 people, seven train / three test; NODDI: 17, two held out. Cortical maps report SSIM &gt;0.6735, temporal cosine about 0.85 and CCC about 0.8; CCC axes/aggregation need clarification. The separate CCC 0.98589-0.98714 super-resolution result uses <b>measured low-resolution BOLD</b>. Parkinson classification without paired BOLD does not validate reconstructed patient signals. Code/weights unverified." + cite("CATD: author full text", "https://arxiv.org/html/2408.00777"))
model("Qu et al. | CVPR 2026", "Six CineBrain people, person-specific models, approximately 288 training / 72 test minutes each with unseen video clips. Predicts 91,282 grayordinates, spatial r 0.824 and MSE 0.277 over ten-frame sequences. This is not unseen-person, per-voxel temporal R. Separate interpolation uses real fMRI anchors; code/weights unverified." + cite("Qu et al.: high-resolution brain dynamics, CVPR 2026", "https://openaccess.thecvf.com/content/CVPR2026/papers/Qu_Modeling_Spatiotemporal_Neural_Frames_for_High_Resolution_Brain_Dynamic_CVPR_2026_paper.pdf"))
model("NT-ViT / E2fNet | ECCV workshop 2024 / EMBC 2025", "Volumetric LOSO SSIM on NODDI (15 analyzed people) / Oddball (17): NT-ViT 0.581 / 0.627, E2fNet 0.605 / 0.631. E2fNet also tests CN-EPFL, 20 people with a 16/4 split. Separate preprocessing prevents pooled ranking; image similarity does not establish temporal fidelity. E2fNet's dataset-wide EEG normalization needs audit. Code exists; trained weights unverified." + cite("NT-ViT: original paper", "https://arxiv.org/html/2409.11836") + cite("E2fNet: original paper", "https://arxiv.org/html/2502.08025"))
model("BEIRA | 2022 preprint", "Eight people, two scanners, individually fitted on four minutes and tested on the last minute. Four bilateral basal-ganglia targets: temporal R 0.44 ± 0.05 vs ridge 0.24 ± 0.11. Requires personal fMRI training; upsampling BOLD to 100 Hz adds no independent observations." + cite("BEIRA: original preprint", "https://arxiv.org/pdf/2211.02024"))
model("Herzog et al. / Mehta et al. | 2026", "Herzog: 19 healthy men, leave-one-run-out with the same people retained in training; ventral-striatal R 0.323 vs linear 0.213. Mehta, revised preprint: 15 personally calibrated people, two sessions; cross-session significant prediction in 13/15 in each task condition but 7/15 at rest. Counts of significance are not correlation magnitudes." + cite("Herzog et al.: Imaging Neuroscience 2026", "https://pure.mpg.de/rest/items/item_3697967_1/component/file_3697968/content") + cite("Mehta et al.: session-transfer preprint", "https://arxiv.org/html/2504.10752"))

# 5. Limits and decomposition.
section("04", "Which blockers can a bigger model fix?")
add("Let <b>X</b> contain exactly the information available at deployment: EEG history, permitted physiology, preprocessing and any personal calibration. Let <b>Y</b> be a specified measured BOLD value. Under squared error and finite variance, the best average prediction is <b>m(X) = E[Y | X]</b>.")
story.append(Diagram("errors",183))
add("Figure 3. Exact decomposition: E[(Y - f(X))²] = E[Var(Y | X)] + E[(m(X) - f(X))²]. The conceptual distinction supplies no numerical EEG-to-fMRI ceiling.","caption")
table(["Source of difficulty", "What could resolve it"], [
    ["<b>Spatial mixing and cancellation.</b> Different sources can produce indistinguishable scalp inputs.", "Test nested montages, electrode locations and anatomy. A fundamental limit applies only when invisible differences change the chosen target."],
    ["<b>Missing physiology.</b> Respiration, CO2 and autonomic state can change BOLD given EEG.", "Compare EEG-only, physiology-only and combined models. The conditional value of each sensor remains unmeasured."],
    ["<b>Vascular variation and pathology.</b> Individual haemodynamic response functions (HRFs) and neurovascular uncoupling alter EEG-to-BOLD coupling.", "Repeat-day calibration, vascular assessment and indication-specific patients. A healthy prior cannot certify lesion-adjacent function."],
    ["<b>Representation, artifacts and fitting.</b> Lost features, scanner contamination, small samples or leakage.", "Feature/context ablations; artifact references; causal preprocessing; person/site holdouts and controlled capacity curves."],
], [CW*.47,CW*.53])
add("Deep sources are not categorically invisible: selected subcortical alpha activity has been detected with dense EEG. Conversely, detecting a source does not establish complete recovery of its BOLD trajectory. Intracranial phase/broadband findings also do not guarantee clean scalp predictors." + cite("Ahlfors et al.: cancellation in EEG/MEG", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2797557/") + cite("Seeber et al.: subcortical EEG source detection", "https://www.nature.com/articles/s41467-019-08725-w") + cite("Hermes et al.: synchrony and metabolism", "https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.2001461"), "small")
add("Key physiology: CO2-related BOLD changes, variable haemodynamic responses and brain-body coupling motivate direct measurement rather than an assumption that extra parameters will absorb them." + cite("Wise et al.: CO2 and resting BOLD", "https://pubmed.ncbi.nlm.nih.gov/15050588/") + cite("Handwerker et al.: haemodynamic response variation", "https://pubmed.ncbi.nlm.nih.gov/15050587/") + cite("Bolt et al.: brain-body coupling", "https://www.nature.com/articles/s41593-025-01945-y") + cite("Agarwal et al.: neurovascular uncoupling in glioma", "https://doi.org/10.1002/jmri.25012"),"small")

# 6. Interpretation and internal data.
section("05", "Know what the results do - and do not - explain")
sub("Correlation is not a calibrated reconstruction")
add("A prediction can have perfect correlation yet be too large, shifted in level, or clinically misleading in amplitude. Report temporal r together with held-out predictive <b>R² = 1 - SSE/SST</b>, naming the baseline and aggregation. Predictive R² can be negative. <b>Squaring mean(r) is neither calibrated R² nor the fraction of neural variance recovered.</b>")
add("SSE is the summed squared prediction error; SST is the summed squared deviation from the chosen mean baseline. The ratio asks whether prediction improves squared error over that baseline.","small")
sub("Noise reliability and EEG observability are different limits")
add("For repeated measurements of the <i>same</i> underlying signal, Y<sub>1</sub> = S + e<sub>1</sub> and Y<sub>2</sub> = S + e<sub>2</sub>, independent equal-variance errors give reliability ρ = Corr(Y<sub>1</sub>,Y<sub>2</sub>). Predicting S against one noisy measurement has correlation ceiling √ρ under those assumptions. Separate resting visits do not repeat the same spontaneous trajectory; multi-echo data need a correlated-noise model. No project noise ceiling has been measured." + cite("Lage-Castellanos et al.: estimating prediction noise ceilings", "https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006397"))
add("The separate oracle identity <b>r<sub>max</sub>² = Var(E[Y | X]) / Var(Y)</b> is an input-specific mathematical limit. It cannot supply a numerical ceiling without estimating those quantities. Realistic generative samples can express a plausible outcome without identifying what happened in this patient." + cite("Blau and Michaeli: perception-distortion tradeoff", "https://openaccess.thecvf.com/content_cvpr_2018/html/Blau_The_Perception-Distortion_Tradeoff_CVPR_2018_paper.html"))
sub("What our own project contributes")
table(["Exploratory project finding", "Interpretation to communicate"], [
    ["VU, 22 people, grouped CV: ridge R 0.381 vs shared 24 s NeuroBOLT 0.336.", "Tuned simple models are essential comparators. This does not prove universal linear sufficiency."],
    ["64-region mean R: 0.343 before global-signal removal, 0.144 after.", "Test regional residual specificity. The removed signal is not thereby proven to be artifact."],
    ["Frozen ds006040 ridge, 28 people: eyes-closed R 0.227 vs within-site 0.228; eyes-open 0.140.", "Close estimates are not equivalence, nor an explanation of the accuracy drop."],
    ["Cleaned-EEG streaming replay: global-BOLD r 0.263; about 3 ms computation per volume.", "Replay and compute timing do not establish live cleaning or clinical alert latency. Context is 24 s; target is delayed BOLD."],
], [CW*.48,CW*.52])
add("Project evidence is exploratory and not independently peer reviewed. A small learning-curve plateau does not identify an irreducible biological ceiling. Full local reports preserve the definitions, splits and failure analyses.","caption")
callout("A claim worth testing", "Does an EEG model preserve an individual's regional contrast or abnormal response beyond global-state, physiology-only and task-only baselines? That is a stronger test of specificity than a convincing whole-brain picture.")

# 7. Clinical route.
section("06", "Choose the clinical action before the model")
table(["Possible application", "Required evidence beyond BOLD correlation"], [
    ["<b>Wakefulness advisory</b><br/>Technologist reviews sustained loss of wakefulness during a specified adult scan.", "Independent sleep/pupil/eyelid/behaviour reference; event sensitivity, false alarms/hour, delay, calibration, coverage and failed recordings. Acquisition benefit needs scan-quality and workflow outcomes."],
    ["<b>One regional feedback target</b><br/>A specified supervised intervention.", "Target sign, amplitude, lag and between-day agreement against real fMRI; then controlled symptom/function outcomes, durability and harms. Treatment benefit and exact ROI recovery are separate claims."],
    ["<b>One imaging decision</b><br/>For example, specified language lateralization.", "Wrong-sided decisions, missed critical sites, localization error and abstention against appropriate clinical evidence and follow-up. Preserve anatomical MRI and escalation pathways."],
], [174,CW-174])
sub("A real clinical precedent: Prism / Amyg-EFP")
add("FDA K222101, cleared 17 March 2023, covers EEG biofeedback for relaxation/stress reduction and adjunctive PTSD symptom treatment under professional supervision alongside other care. It explicitly excludes diagnostic conclusions, classification and clinical interpretation. <b>This is not clearance of diagnostic fMRI replacement.</b>" + cite("FDA: Prism K222101 clearance and clinical summary", "https://www.accessdata.fda.gov/cdrh_docs/pdf22/K222101.pdf"))
add("The supporting five-site single-arm study had 79 full-analysis patients, 66 in the efficacy set and 63 per protocol; 66.67% of the efficacy set achieved ≥6-point CAPS-5 improvement at three months. Without a control, that result cannot isolate efficacy; the journal paper and regulatory summary describe the same trial. A separate randomized proof-of-concept study included 59 adults but leaves mechanism/placebo questions." + cite("Fruchter et al.: clinical Prism study, 2024", "https://doi.org/10.1016/j.psychres.2023.115711") + cite("Fruchtman-Steinbok et al.: randomized PTSD proof of concept", "https://pmc.ncbi.nlm.nih.gov/articles/PMC8551212/"),"small")
story.append(Diagram("gates",130))
add("Figure 4. Proposed translation pathway. External technical accuracy, live workflow performance and clinical benefit are distinct validation gates." + cite("IMDRF N41: clinical evaluation of medical device software", "https://www.imdrf.org/sites/default/files/docs/imdrf/final/technical/imdrf-tech-170921-samd-n41-clinical-evaluation_1.pdf") + cite("DECIDE-AI: early clinical evaluation reporting guideline", "https://www.bmj.com/content/377/bmj-2022-070904.long"),"caption")

# 8. Datasets and model envelopes.
section("07", "How much paired data and model capacity?")
add("<b>No directly relevant EEG-to-BOLD scaling law was verified.</b> More windows do not create more independent patients. The inventories below are starting points for QC, not a harmonized clinical training corpus.")
table(["Public release", "Audited inventory and limitation"], [
    ["ds006040", "28 people, one visit; 27.92 nominal paired hours, including 5.60 h rest. Protocol totals precede synchronization/QC." + cite("ds006040: dataset descriptor", "https://www.nature.com/articles/s41597-026-06616-6")],
    ["ds003768", "33 people; 66 ten-minute rest and 189 fifteen-minute sleep runs: 58.25 nominal protocol hours." + cite("ds003768: resting and sleep dataset descriptor", "https://doi.org/10.1016/j.dib.2023.109059")],
    ["MULTI-CLARID / ds005795", "34 people; 34 ten-minute resting pairs and five public 27-minute task pairs: about 7.92 nominal hours." + cite("MULTI-CLARID: pinned public README and manifest", "https://github.com/OpenNeuroDatasets/ds005795/blob/a225eb4608bd72e20a6aa6aa6fdda09692f77a7f/README")],
    ["NIH sleep1 / ds005127", "16 people, 29 person-session directories, 175.05 recorded EEG hours. Synchronized usable paired hours unresolved. LICENSE/metadata conflict: retain attribution and clarify." + cite("NIH sleep1: pinned dataset inventory", "https://github.com/OpenNeuroDatasets/ds005127/tree/5b7ded720e22ba57bf402c80bf48508274062f79")],
    ["NATVIEW", "22 adults; repeat visits intended. Complete usable-hour inventory remains unverified. Do not sum releases before deduplication and QC." + cite("NATVIEW: dataset descriptor", "https://www.nature.com/articles/s41597-023-02458-8")],
], [142,CW-142])
sub("Development envelopes - proposals, not sufficient thresholds")
table(["Programme", "People / sites", "Paired acquired → usable hours*"], [
    ["Measurement pilot", "40-80 / 2", "Two 30 min visits: 40-80 → 30-60 h"],
    ["Arousal advisory", "150-300 / 2-4", "Two 30 min visits: 150-300 → 112.5-225 h"],
    ["One feedback target", "300-600 / 3-5", "Two 45 min visits: 450-900 → 337.5-675 h"],
    ["Regional feasibility", "200-400 / 3-5", "Two 45 min visits: 300-600 → 225-450 h"],
    ["Conditional broader regions", "1,000+ / 8-12", "At 1,000: 1,500 → 1,125 h; only after positive gates"],
    ["Separate frozen validation", "200-400 NEW / 3-5 NEW", "Two 45 min visits: 300-600 → 225-450 h"],
], [150,137,CW-287])
add("*Assumes all visits completed and hypothetical 75% paired-time retention. Pilot is included in development totals; programme rows are alternatives/conditional, not additive. Validation adds new patients. Clinical arousal labels and therapeutic follow-up need separate budgets.","caption")
add("Start with ridge/kernels and compact neural comparators: proposed 0.1-3M parameters for arousal, 0.1-10M for one-region feedback. Existing MARBLE (2.6M) and UnEBOLT (8.2M) show that enormous networks are not a prerequisite. Broader replacement has no defensible required N or sufficient parameter count. Adjacent fMRI scaling research does not provide that missing law." + cite("Ooi et al.: adjacent fMRI phenotype scaling study, 2025", "https://doi.org/10.1038/s41586-025-09250-1"),"small")

# 9. Clinical sample sizes.
section("08", "Clinical validation size follows the endpoint")
add("Training sufficiency and validation precision are different budgets. For a frozen binary decision, a simple illustrative normal approximation uses <b>n<sub>+</sub> = ceiling[1.96² × Se × (1 - Se) / d²]</b>, where Se is assumed sensitivity and d the desired 95% half-width. Count independent reference-positive people or appropriately defined events." + cite("Buderer 1996: diagnostic sample-size planning", "https://pubmed.ncbi.nlm.nih.gov/8870764/"))
table(["Assumptions", "Required class denominator", "Expected accrual at 10% positivity"], [
    ["Sensitivity 90%, ±5 points", "139 positives", "1,390 before loss/clustering"],
    ["Sensitivity 90%, ±3 points", "385 positives", "3,850 before loss/clustering"],
    ["Specificity 95%, ±3 points", "203 negatives", "Check negative yield separately"],
], [170,150,CW-320])
add("The assumed 10% is endpoint positivity, not a disease prevalence claim. With 15% loss, expected recruitment for the first row is ceiling(1,390/0.85) = <b>1,636</b>. Expected accrual does not guarantee enough positives. Final planning needs Wilson/exact intervals; estimating near 90% does not prove sensitivity exceeds 90%. These figures are not regulatory minimums." + cite("FDA: reporting diagnostic test study results", "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/statistical-guidance-reporting-results-studies-evaluating-diagnostic-tests-guidance-industry-and-fda"))
sub("Repeated events do not replace independent patients")
add("Ten events per person with within-person ICC 0.20 give design effect 1 + 9(0.20) = <b>2.8</b>. About 390 observed events approximate 139 independent events under that illustration, without ensuring patient diversity. Site clustering and systematic site shift require their own design." + cite("Cluster-design methods: dependence and design effects", "https://academic.oup.com/ije/article/44/3/1051/632956"))
sub("A high sensitivity can still produce many false alerts")
table(["Illustrative sensitivity 90%, specificity 95%", "Positive predictive value"], [
    ["Endpoint prevalence 10%", "66.7%"],
    ["Endpoint prevalence 1%", "15.4%"],
], [CW-153,153])
add("For monitoring, measure actual false alarms/hour and event-delay distributions rather than relying on PPV alone. Provisionally consider 4-6 external sites for a narrow programme, then size independent denominators using pilot prevalence and dependence. Include failures and abstentions across all enrolled patients.")
add("For a controlled therapeutic study, equal independent arms, alpha 0.05, 80% power and effect size 0.5-0.3 imply roughly <b>126-350 analyzable patients</b>; these are hypothetical inputs. Zero harmful events in 300 independent cases only bounds risk at about 1% (one-sided 95%). Presurgical decisions need agreed error margins before sizing. TGA/IMDRF provide no universal EEG-fMRI R or N threshold." + cite("TGA: evidence requirements for AI software", "https://www.tga.gov.au/products/medical-devices/software-and-artificial-intelligence-ai/manufacturing/artificial-intelligence-ai-and-medical-device-software-regulation/evidence-requirements-software-using-ai"),"small")

# 10. Research design and resources.
section("09", "What to run next on Monash M3")
add("The useful next study crosses <b>training people × minutes/person × available measurements × model capacity</b> while holding evaluation cases fixed. VU and ds006040 are already development data; reserve a genuinely untouched release before inspecting outcomes.")
story.append(Diagram("study",208))
add("Figure 5. A proposed experiment that distinguishes model limitations from information limitations. Sensor comparisons use only jointly available measurements; a respiration belt does not measure end-tidal CO2.","caption")
sub("Make the result interpretable")
add("Compare tuned lagged ridge, the shared spectral/lag kernel and one compact neural candidate, such as a reproducible MARBLE or UniEFS implementation. Match folds and causal history. Include physiology-only, task-only and global-template controls. Report full BOLD and explicitly defined global/physiology-adjusted regional residual targets; residual skill is not a pure neural fraction.")
add("Group repeated visits; split before learned preprocessing; audit filters, normalization and future-data access. Use nested tuning, person-level uncertainty and appropriate temporal surrogates. Report site variation. A repeatedly inspected development holdout is not the final clinical test, and a nonsignificant difference is not equivalence.")
sub("Compute and acquisition are different resources")
add("Begin with CPU QC/features/ridge and <b>one compact GPU experiment at a time</b>. Profile one fold/seed and several capacities. Two candidates × five folds × three seeds = <b>30 fits</b>; compute budget = 30 × measured GPU-hours/fit. Log RAM/VRAM, preprocessing time and derivative storage rather than assuming a fixed cluster cost.")
add("At 64 channels × 5,000 samples/s × 4 bytes, EEG alone is <b>4.61 GB/hour</b>; 1,500 acquired hours are about <b>6.9 TB</b>, before MRI, auxiliary signals, derivatives and backups. Actual format and sampling change this figure. Scanner bookings also include preparation, failures and repeated acquisition. Obtain local combined EEG-fMRI and staffing quotes.")
callout("Go / no-go decision", "Advance arousal only after external causal predictions meet clinician-defined false-alarm, delay and coverage limits; then test prospectively. Advance regional synthesis only after patient-specific contrasts and abnormal responses survive strong simple/global/physiology baselines across visits and sites. Scale toward 1,000+ people only while useful gains justify it.")

# 11. Human learning and communication.
section("10", "What you and the human team need to own")
add("The central research question is not simply whether a network can draw a brain. It is <b>which clinically relevant information EEG contains, what added measurements reveal, and whether using the estimate improves a real decision</b>.")
table(["Human investigator / collaborator", "Question or decision to own"], [
    ["MR physicist + EEG specialist", "Are clocks aligned and acquisition safe? Does prospective artifact correction preserve neural information? Does performance transfer out of the scanner?"],
    ["Sleep/arousal investigator + technologist + patients", "What counts as an event, what independent reference confirms it, and what alert burden/action is acceptable? EEG-derived labels need independence documentation and non-EEG corroboration."],
    ["Psychiatrist / neurofeedback investigator", "Does the named target engage the proposed mechanism? Which comparator separates feedback from expectancy/exposure? Are outcomes durable and harms tracked?"],
    ["Neurologist / neuroradiologist / surgical team", "Which regional error would change care? Are lesion-adjacent abnormalities preserved, and how are discrepancies adjudicated?"],
    ["Biostatistician + clinical coordinator", "What independent denominators, site diversity, error margins and missing-data plans support the exact claim? What recruitment, ethics and QC resources are required?"],
], [174,CW-174])
sub("Curate your own learning in this order")
add("<b>1. Measurement:</b> explain EEG mixtures, BOLD delay and vascular confounds. <b>2. Evaluation:</b> distinguish time, space and connectivity; calibration, repeated windows and independent patients. <b>3. Inference:</b> understand conditional expectation and the two error terms. <b>4. Clinical translation:</b> name one action, comparator, failure cost and evidence gate.")
add("Use AI to organize evidence, audit calculations, build reproducible analyses and expose assumptions. Human researchers must verify cited claims and protocols, inspect patient-specific failures, choose clinical error limits and design missing physiological measurements. A plausible generated explanation cannot resolve an unmeasured quantity; a mathematical bound cannot supply an empirical ceiling without its assumptions and estimates.")
callout("A concise explanation for stakeholders", '"We can predict some brain-state-related fMRI dynamics from EEG. New methods improve regional prediction, but no result here establishes dependable patient-specific scan replacement. We will test a narrow application against independent ground truth, compare simple models with compact neural models, and measure whether added physiology helps more than added capacity. Further investment depends on external accuracy and prospective clinical usefulness."')
add("New CO2 or cerebrovascular-reactivity (CVR) measurements, repeat-day calibration and recruitment of relevant patient groups need human-led protocols and ethics. M3 supplies computation, not those measurements or clinical adjudication.","small")

# References: clickable titles; compact enough to read in print.
section("SOURCES", "Primary reading and provenance")
add("Numbers link to the original papers, datasets or official documents used in the source audit. Preprints are identified above. Publication values have not been independently reproduced in this PDF; unresolved access, split and aggregation issues remain unresolved.","small")
for n,(title,url) in enumerate(REFS,1):
    domain=re.sub(r"^https?://", "", url).split("/")[0]
    add(f'<b>[{n}]</b> <a href="{escape(url,quote=True)}" color="#007F82">{escape(title)}</a><br/><font color="#566878">{escape(domain)}</font>',"ref")
sub("Project source material")
add("Full narrative audit: <b>reports/Clinical EEG to fMRI feasibility.md</b>. Detailed reading notes: <b>research_notes/Clinical EEG to fMRI feasibility/</b>. Internal interpretability and external-validation reports are project provenance, not independent confirmations. The full audit retains supplementary sources, repository/access links and unresolved inventory details.","small")
add("Evidence cutoff: 21 October 2026. This is a research planning brief. Proposed cohorts, parameter brackets, retention rates, endpoint prevalence and compute formulas are explicit design assumptions, not observed clinical performance or regulatory requirements. Diagrams are explanatory schematics, not evidence of efficacy.","caption")

class NumberedCanvas(canvas.Canvas):
    def __init__(self,*args,**kwargs):
        canvas.Canvas.__init__(self,*args,**kwargs)
        self._saved_pages=[]
    def showPage(self):
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        total=len(self._saved_pages)
        for page_state in self._saved_pages:
            self.__dict__.update(page_state)
            self.setFillColor(MUTED);self.setFont("Arial",8)
            self.drawRightString(W-M,27,f"{self._pageNumber} / {total}")
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

def page(c,doc):
    c.saveState()
    c.setStrokeColor(LINE);c.setLineWidth(.5)
    c.line(M,H-35,W-M,H-35);c.line(M,43,W-M,43)
    c.setFillColor(MUTED);c.setFont("Arial",7.5)
    running = "NEUROBOLT  /  CLINICAL EEG-TO-fMRI FEASIBILITY"
    if doc.page >= 13:
        running = "NEUROBOLT  /  PRIMARY SOURCES (CONTINUED)"
    c.drawString(M,H-26,running)
    c.drawRightString(W-M,H-26,"21 OCT 2026")
    c.drawString(M,27,"Research evidence + proposed clinical development plan")
    c.restoreState()

doc=BaseDocTemplate(str(OUT),pagesize=(W,H),leftMargin=M,rightMargin=M,topMargin=49,bottomMargin=56,
                    title="Clinical EEG-to-fMRI feasibility: evidence, limits and research plan",
                    author="NeuroBOLT research project",subject="Illustrated evidence briefing; 21 October 2026")
doc.addPageTemplates(PageTemplate(id="main",frames=[Frame(M,56,CW,H-105,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=page))
doc.build(story,canvasmaker=NumberedCanvas)
print(f"Created {OUT}")
print(f"References: {len(REFS)}")
