"""Write the advisor deck (Slides artifact 7GYCMZdTARY5JXeQwe5Fjc) in a Monash research-talk style.

Every content slide shares one template: bold Arial title, section tracker, purple rule, grey content
panel, footer with the university and the slide number. Output: deck/project/{deck.json,slides/*.html}.
"""
import json
import os
import sys

ROOT = sys.argv[1]
OUT = os.path.join(ROOT, "project")
os.makedirs(os.path.join(OUT, "slides"), exist_ok=True)

INK, MUTED, PURPLE, PANEL, SUB = "#1a1a1a", "#7a7a7a", "#5e3a87", "#e9e9e9", "#3a3a3a"
FONT = "Arial, Helvetica, sans-serif"
SECTIONS = ["Background", "Methods", "Results", "Application", "Conclusions"]
A = {  # uploaded figure assets in this deck
    "nulls": "/_blob/a2c0166966ad84a96de6dc6998d9460c", "brain": "/_blob/5eb9bdf836c2dc162d1dd93346df6bd7",
    "brain_gsr": "/_blob/398729df2d2a46c6bb779d49b6f6fc14", "loading": "/_blob/08269fe5d1d13ff86f8a6399603971b1",
    "coupling": "/_blob/a653c76e0fcca7ff806a6e8bf64b7fe4", "physio": "/_blob/126da628826c61dbeaf50e7a2a0d8543",
    "ext": "/_blob/e1d38efbfe21a96a0b2659503da329f6", "monitor": "/_blob/360bd0e74d03dfc44dd8374e6bfb8e23",
}


def tracker(current):
    if not current:
        return ""
    parts = [f'<span style="color:{PURPLE};font-weight:700">{s}</span>' if s == current else s for s in SECTIONS]
    return (f'<p style="position:absolute;right:96px;top:34px;width:1300px;text-align:right;font-size:24px;'
            f'letter-spacing:1px;text-transform:uppercase;color:#a3a3a3">' + " &#160;·&#160; ".join(parts) + "</p>\n")


def bullets(items, size=34, sub=28, gap=22):
    out = [f'<div style="display:flex;flex-direction:column;gap:{gap}px;flex:1;min-width:0">']
    for item in items:
        text, subs = (item, []) if isinstance(item, str) else item
        out.append(f'<ul style="font-size:{size}px;line-height:1.3;color:{INK};padding-left:40px"><li>{text}</li></ul>')
        if subs:
            out.append(f'<ul style="font-size:{sub}px;line-height:1.3;color:{SUB};padding-left:92px">'
                       + "".join(f"<li>{s}</li>" for s in subs) + "</ul>")
    out.append("</div>")
    return "".join(out)


def figure(src, alt, w, h, caption=None):
    cap = (f'<p style="font-size:24px;color:{MUTED};line-height:1.3;width:{w}px">{caption}</p>' if caption else "")
    return (f'<div style="display:flex;flex-direction:column;gap:10px">'
            f'<img src="{src}" alt="{alt}" style="width:{w}px;height:{h}px;object-fit:contain;background:#ffffff;'
            f'border:1px solid #cfcfcf">{cap}</div>')


def content(sid, num, section, title, body, notes, panel_style="display:flex;gap:48px;align-items:center"):
    return (f'<section id="{sid}" data-transition="fade" style="background:#ffffff;color:{INK};font-family:{FONT};'
            f'padding:84px 96px 132px;display:flex;flex-direction:column;gap:24px">\n'
            f'{tracker(section)}'
            f'<h2 style="font-family:{FONT};font-size:64px;font-weight:700;line-height:1.1;color:{INK}">{title}</h2>\n'
            f'<div style="height:10px;background:{PURPLE}"></div>\n'
            f'<div style="flex:1;background:{PANEL};padding:44px 56px;border-radius:0 0 28px 0;{panel_style}">{body}</div>\n'
            f'<p style="position:absolute;left:96px;bottom:44px;width:1100px;font-size:24px;color:{MUTED}">'
            f'<b>Monash University</b> &#160;·&#160; Faculty of Information Technology</p>\n'
            f'<p style="position:absolute;right:96px;bottom:44px;width:200px;font-size:24px;color:{MUTED};text-align:right">{num}</p>\n'
            f'<aside>{notes}</aside>\n</section>\n')


slides = []

# 1 · title (the Hart Talk layout: header, purple rule, grey title band)
slides.append(("title", f"""<section id="title" data-transition="fade" style="background:#ffffff;color:{INK};font-family:{FONT};padding:0;display:flex;flex-direction:column">
<div style="padding:64px 96px 0;height:270px;display:flex;flex-direction:column;gap:6px">
<p style="font-size:44px;font-weight:700;color:{INK}">Monash University</p>
<p style="font-size:30px;color:{PURPLE}">Faculty of Information Technology</p>
</div>
<div style="height:14px;background:{PURPLE}"></div>
<div style="flex:1;background:{PANEL};display:flex;flex-direction:column;justify-content:center;align-items:center;gap:30px;padding:0 160px">
<h1 style="font-family:{FONT};font-size:80px;font-weight:700;line-height:1.1;text-align:center;color:{INK}">What EEG-to-BOLD Models Actually Learn</h1>
<p style="font-size:40px;line-height:1.3;text-align:center;color:{SUB}">Can scalp EEG predict deep brain activity in people a model has never seen?</p>
<p style="font-size:32px;line-height:1.4;text-align:center;color:{INK}">Seamus Taylor &#160;·&#160; [Student ID]<br>Supervisor: [Supervisor name]</p>
</div>
<div style="height:120px;padding:0 96px;display:flex;justify-content:space-between;align-items:center">
<p style="font-size:26px;color:{MUTED}">[Unit code] &#160;·&#160; October 2026</p>
<p style="font-size:26px;color:{MUTED}">Computation: Monash MASSIVE M3</p>
</div>
<aside>A reproduction and dissection of NeuroBOLT, an EEG-to-fMRI transformer from NeurIPS 2024, on its own data and on a second site, plus a prototype built on what we learned.</aside>
</section>
"""))

# 2 · overview
slides.append(("overview", content("overview", 2, None, "Overview", bullets([
    "Background and research motivation",
    "Research questions",
    "Research methods",
    ("Results", ["Is the prediction real, and where in the brain?", "What do the models read?",
                 "Brain or body? Does nonlinearity help?", "Does it hold on a new dataset?"]),
    "Application: an EEG arousal monitor",
    "Findings, implications and further research",
], gap=24), "The talk follows the usual research arc: background, questions, methods, results, an application, and what it means.",
    panel_style="display:flex;align-items:start")))

# 3 · background
slides.append(("background", content("background", 3, "Background", "Background", bullets([
    ("EEG and fMRI watch the brain in different ways", ["EEG: scalp electrodes, millisecond timing, cheap and portable",
                                                       "fMRI (BOLD): whole brain incl. deep regions, but slow and needs a scanner"]),
    ("Predicting fMRI from EEG would let us monitor deep brain activity outside the scanner", [
        "Sleep labs, bedside, neurofeedback, long recordings"]),
    ("NeuroBOLT (Li et al., NeurIPS 2024)", ["Pretrained EEG transformer (LaBraM) + spectral branch",
                                            "Reported mean R = 0.473 for 7 regions in 5 held-out people"]),
    "The test that matters: predict BOLD in a person the model has never seen",
]), "EEG is cheap and fast but sees only the scalp; fMRI sees the whole brain including the thalamus, but slowly and only in a scanner. NeuroBOLT claimed EEG alone can predict fMRI in new people.",
    panel_style="display:flex;align-items:start")))

# 4 · motivation with a bar chart drawn from divs
bars = [("NeuroBOLT, paper's split<br>(5 people)", 0.473, "#a99bc4"), ("NeuroBOLT, all<br>22 people", 0.336, "#a99bc4"),
        ("Ridge regression, all<br>22 people", 0.381, PURPLE)]
chart = ['<div style="display:flex;flex-direction:column;gap:12px;width:820px">',
         f'<p style="font-size:28px;font-weight:700;color:{INK}">Mean R, held-out people (7 regions)</p>',
         '<div style="display:flex;align-items:end;gap:56px;height:440px;padding:0 24px;border-bottom:2px solid #9a9a9a">']
for label, value, color in bars:
    chart.append(f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:8px">'
                 f'<p style="font-size:30px;font-weight:700;color:{INK}">{value:.3f}</p>'
                 f'<div style="width:150px;height:{int(value * 800)}px;background:{color}"></div></div>')
chart.append('</div><div style="display:flex;gap:56px;padding:0 24px">')
for label, value, color in bars:
    chart.append(f'<p style="flex:1;font-size:24px;line-height:1.25;text-align:center;color:{SUB}">{label}</p>')
chart.append("</div></div>")
slides.append(("motivation", content("motivation", 4, "Background", "Research Motivation", "".join(chart) + bullets([
    ("Our reproduction matched the paper on its own split", ["But that split is the easiest of five"]),
    ("Across all 22 people, simple ridge regression beats NeuroBOLT", ["For 19–20 of 22 people"]),
    "NeuroBOLT’s pretrained transformer branch adds nothing",
    "So what are these models actually learning?",
], size=32, sub=26), "Earlier work in this project reproduced NeuroBOLT and found a linear model does better across people. That raises the question this talk answers.")))

# 5 · research questions
slides.append(("questions_rq", content("questions_rq", 5, "Background", "Research Questions", bullets([
    "RQ1. Is the prediction real, or an artefact of the evaluation?",
    "RQ2. Where in the brain is BOLD predictable from EEG?",
    "RQ3. Which EEG features, and which time lags, carry the signal?",
    "RQ4. What does the NeuroBOLT transformer actually learn?",
    "RQ5. Brain or body: do heart, eye and muscle signals explain it?",
    "RQ6. Does nonlinear modelling help with 13–21 training people?",
    "RQ7. Does it hold on a new dataset from another site?",
], gap=26), "Seven questions, each answered with its own analysis on Monash M3.",
    panel_style="display:flex;align-items:start")))

# 6 · methods with a flow of boxes and arrows
flow = ['<div style="display:flex;flex-direction:column;gap:40px;width:100%">',
        '<div style="display:flex;align-items:center;gap:20px">']
steps = [("Scalp EEG", "26 channels, 24 s before each fMRI frame"), ("Spectral features", "log power, 1–45 Hz, 12 lags"),
         ("Model", "ridge regression or NeuroBOLT"), ("BOLD", "64 regions + global signal")]
for i, (head, sub) in enumerate(steps):
    if i:
        flow.append(f'<x-shape kind="arrow-right" style="width:64px;height:36px;background:{PURPLE}"></x-shape>')
    flow.append(f'<div style="flex:1;background:#ffffff;border:2px solid {PURPLE};border-radius:12px;padding:22px 24px;'
                f'display:flex;flex-direction:column;gap:6px"><p style="font-size:30px;font-weight:700;color:{INK}">{head}</p>'
                f'<p style="font-size:24px;line-height:1.3;color:{SUB}">{sub}</p></div>')
flow.append("</div>")
flow.append('<div style="display:flex;gap:56px">')
flow.append(bullets([("Data", ["VU dataset: 22 people, 29 eyes-closed scans", "ds006040: 28 new people, another site"]),
                     ("Evaluation", ["5-fold cross-validation grouped by person", "Score only on people the model never saw"])],
                    size=30, sub=26, gap=14))
flow.append(bullets([("Controls", ["Null models: shifted and mismatched BOLD", "Heart, eye, muscle and head-motion channels"]),
                     ("Interpretation", ["Coupling maps, linear surrogates, permutation tests", "Computation on Monash MASSIVE M3"])],
                    size=30, sub=26, gap=14))
flow.append("</div></div>")
slides.append(("methods", content("methods", 6, "Methods", "Research Methods", "".join(flow),
    "Each fMRI frame is predicted from the 24 seconds of EEG before it, so the model is causal. Every score comes from people the model never saw; the real sample size is people, not frames.",
    panel_style="display:flex;align-items:center")))

# 7–14 · results
res = [
    ("res_real", "Results: The Prediction Is Real", figure(A["nulls"], "Per-scan ridge R against two null distributions", 980, 474,
        "Orange: each held-out scan. Grey: chance levels."), bullets([
        "28 of 29 scans beat their own null", ("Mismatched-person null: R = 0.00", ["One person’s prediction vs another person’s BOLD"]),
        "No shared drift inflates the result"], size=32, sub=26),
     "Slow signals correlate by chance, so each scan gets its own null. The decisive check scores one person's prediction against another person's BOLD: it gives zero."),
    ("res_where", "Results: Where in the Brain?", '<div style="display:flex;flex-direction:column;gap:16px">'
        + figure(A["brain"], "Ridge R in every brain region", 1000, 230, "Cross-subject ridge R in 64 regions (darker = better)")
        + figure(A["loading"], "Predictability against global-signal loading", 900, 353) + "</div>", bullets([
        ("Sensory and motor cortex best", ["R ≈ 0.43", "Default and control regions ≈ 0.27"]),
        ("Predictability follows the global signal", ["ρ = +0.65 across 64 regions"]),
        "This is the signature of arousal"], size=32, sub=26),
     "A region is predictable to the extent it follows the brain-wide global signal, which tracks arousal."),
    ("res_specific", "Results: Beyond the Global Signal", figure(A["brain_gsr"], "Ridge R after global-signal regression", 1060, 244,
        "R after removing the global signal from every region"), bullets([
        ("Removing the global signal: R 0.34 → 0.14", ["Still far above chance"]),
        ("Best region-specific targets", ["Thalamus 0.28", "Cerebellum 0.26", "Mid-anterior cingulate 0.23"]),
        "Regions whose arousal response opposes cortex"], size=32, sub=26),
     "What survives is region-specific and sits where the arousal literature says it should. No published EEG-to-fMRI study reports this number."),
    ("res_features", "Results: Which Features, When?", figure(A["coupling"], "EEG power by frequency and lag against BOLD", 1060, 387,
        "Blue: more power, lower BOLD. Red: higher BOLD."), bullets([
        "60 band powers keep 93% of the skill", "Textbook HRF shape loses 40%",
        ("Cortex: alpha and beta 9 s earlier, lower BOLD", ["Known inverse alpha coupling"]),
        ("Thalamus: sign flips, 3 s lag", [])], size=30, sub=26),
     "The model reads whole-head band power through the haemodynamic delay. Cortex couples negatively with alpha about 9 seconds earlier; the thalamus positively and sooner."),
]
slides += [(sid, content(sid, 7 + i, "Results", title, fig + text, notes)) for i, (sid, title, fig, text, notes) in enumerate(res)]

# 11 · NeuroBOLT surrogate (table, like the examples' findings slides)
nb_table = f"""<div style="display:flex;flex-direction:column;gap:20px;width:900px">
<table style="font-size:28px;color:{INK};width:900px">
<tr><th style="width:70%;text-align:left">Held-out scans</th><th style="width:30%;text-align:right">R</th></tr>
<tr><td style="text-align:left">Linear imitation vs NeuroBOLT’s own output</td><td style="text-align:right"><b>0.91</b></td></tr>
<tr><td style="text-align:left">NeuroBOLT vs measured BOLD</td><td style="text-align:right">0.465</td></tr>
<tr><td style="text-align:left">Linear imitation vs measured BOLD</td><td style="text-align:right">0.491</td></tr>
<tr><td style="text-align:left">Ridge vs measured BOLD</td><td style="text-align:right">0.504</td></tr>
</table></div>"""
slides.append(("res_neurobolt", content("res_neurobolt", 11, "Results", "Results: What NeuroBOLT Learns", nb_table + bullets([
    ("A ridge model reproduces NeuroBOLT’s output at R = 0.91", ["NeuroBOLT is in effect a linear band-power model"]),
    "The imitation predicts BOLD better than NeuroBOLT",
    ("Scrambling the EEG affects both models alike", ["Last 4 s and 8–12 s matter most"])], size=32, sub=26),
    "A linear map from band power reproduces 83 percent of the variance of NeuroBOLT's predictions; the nonlinear rest is mostly noise.")))

slides.append(("res_body", content("res_body", 12, "Results", "Results: Brain or Body?", figure(A["physio"], "Shared and unique variance of EEG and physiology", 960, 432,
    "Grey: shared. Orange: EEG only. Green: physiology only.") + bullets([
    ("Heart rate alone predicts BOLD: R = 0.22", ["Eye and muscle signals add a little more"]),
    "But EEG already contains all of it", ("Physiology adds almost nothing unique", ["Head-motion sensors add nothing"])], size=32, sub=26),
    "Arousal also changes heart rate, eye movements and muscle tone. These are co-markers of the same state, not separate routes that EEG misses.")))

nl_table = f"""<table style="font-size:28px;color:{INK};width:1700px">
<tr><th style="width:56%;text-align:left">Model (same features)</th><th style="width:16%;text-align:right">R</th><th style="width:28%;text-align:right">vs ridge</th></tr>
<tr><td style="text-align:left">Ridge regression (baseline)</td><td style="text-align:right">0.355</td><td style="text-align:right">–</td></tr>
<tr><td style="text-align:left">Neural network (MLP), leave one person out</td><td style="text-align:right">0.375</td><td style="text-align:right">+0.010, not significant</td></tr>
<tr><td style="text-align:left">Additive splines / vigilance interactions</td><td style="text-align:right">0.347</td><td style="text-align:right">−0.008</td></tr>
<tr><td style="text-align:left">Learned frequency bands, end to end</td><td style="text-align:right">0.355</td><td style="text-align:right">−0.026 vs full ridge</td></tr>
<tr><td style="text-align:left">Person-specific calibration (half the scan)</td><td style="text-align:right">0.406</td><td style="text-align:right">+0.006, not significant</td></tr>
<tr><td style="text-align:left">Interpretable model: 2,040 parameters (vs 892,320)</td><td style="text-align:right">0.329</td><td style="text-align:right">keeps 96% of ridge</td></tr>
</table>"""
slides.append(("res_nonlinear", content("res_nonlinear", 13, "Results", "Results: Does Nonlinearity Help?", nl_table,
    "None of the nonlinear readouts reliably beats ridge. A 2026 preprint claiming a large neural-network gain on these data does not replicate under its own protocol. A compact interpretable model keeps 96 percent of the skill.",
    panel_style="display:flex;align-items:center")))

slides.append(("res_external", content("res_external", 14, "Results", "Results: A New Dataset", figure(A["ext"], "Per-person R on ds006040 for four protocols", 1000, 465,
    "ds006040: 28 people, another site and scanner") + bullets([
    ("Frozen model = model trained there", ["R 0.227 vs 0.228, eyes closed"]),
    ("Lower than on VU (0.23 vs 0.38)", ["Shorter, more alert recordings"]),
    "Eyes open is harder: 0.14", "Ridge still beats NeuroBOLT (0.18)"], size=30, sub=26),
    "The model trained at one site works unchanged on 28 people scanned elsewhere, with no site penalty.")))

# 15 · application
slides.append(("application", content("application", 15, "Application", "Application: EEG Arousal Monitor", figure(A["monitor"], "Predicted and measured global BOLD for one run", 1000, 502,
    "Orange: predicted from EEG. Blue: measured by fMRI.") + bullets([
    ("From EEG alone, every fMRI volume", ["Brain-wide arousal-driven BOLD", "Vigilance trace and flags"]),
    ("Tested on 28 unseen people", ["Tracks fMRI at r = 0.26, also live", "3 ms per volume"]),
    ("Uses", ["Scan quality control", "EEG-only arousal tracking"])], size=30, sub=26),
    "The prototype runs live because each prediction uses only past EEG. Its run-level score tracks the global-signal swing fMRI measured, rho 0.50. The drowsiness flags still need validating.")))

# 16–18 · findings, implications, further research
slides.append(("findings", content("findings", 16, "Conclusions", "Findings", bullets([
    ("The prediction is real and mostly reflects arousal", ["Strongest in regions that follow the global signal"]),
    ("The models read whole-head band power through the blood-flow delay", ["Cortex: alpha 9 s earlier, lower BOLD; thalamus: the opposite"]),
    ("NeuroBOLT learned the same linear map as ridge", ["Its transformer adds nothing"]),
    ("Nonlinear models and calibration do not help at this data size", []),
    ("It holds at a second site, with no penalty", []),
]), "Every analysis points the same way: resting EEG tells us where a person sits on the arousal axis, seen through the haemodynamic delay.",
    panel_style="display:flex;align-items:start")))

slides.append(("implications", content("implications", 17, "Conclusions", "Implications", bullets([
    ("For research", ["Benchmark EEG-to-fMRI models on region-specific signal, not raw BOLD",
                      "Always test against a tuned linear baseline and a mismatched-person null"]),
    ("For model design", ["More capacity is not the bottleneck; diverse people and arousal range are"]),
    ("For applications", ["EEG is a reliable, causal read-out of arousal-driven brain activity",
                          "Useful for fMRI quality control and EEG-only arousal tracking"]),
]), "The ceiling is set by how much arousal moves in a recording, not by the model. That changes what to benchmark and what to build.",
    panel_style="display:flex;align-items:start")))

slides.append(("further", content("further", 18, "Conclusions", "Further Research", bullets([
    ("Region-specific benchmark", ["What does EEG know about a region beyond arousal?"]),
    ("More sites and more people", ["ds005795 (with respiration), ds003768 (with sleep); about 150 people pooled"]),
    ("Wider arousal range", ["Sleep recordings: when do deep models start to pay?"]),
    ("Validate the monitor", ["Eye tracking or sleep scoring; a live pilot in the scanner"]),
]), "Each direction has a result that would change the plan, set out in the research guide.",
    panel_style="display:flex;align-items:start")))

refs = ["Li Y et al. (2024). NeuroBOLT: resting-state EEG-to-fMRI synthesis with multi-dimensional feature mapping. NeurIPS.",
        "Cha et al. (2026). Sustained attention task dataset using simultaneous EEG-fMRI and DTI. Scientific Data; OpenNeuro ds006040.",
        "Goldman RI et al. (2002). Simultaneous EEG and fMRI of the alpha rhythm. NeuroReport 13:2487–2492.",
        "Chang C et al. (2016). Tracking brain arousal fluctuations with fMRI. PNAS 113:4518–4523.",
        "Bolt T et al. (2025). A unified physiological process links global patterns of functional MRI, respiratory activity and autonomic signalling. Nature Neuroscience 28:1327–1335.",
        "Haufe S et al. (2014). On the interpretation of weight vectors of linear models in multivariate neuroimaging. NeuroImage 87:96–110.",
        "Varoquaux G (2018). Cross-validation failure: small sample sizes lead to large error bars. NeuroImage 180:68–77.",
        "Full reports, code and the 117-reference literature review: NeuroBOLT project repository."]
refs_html = (f'<div style="display:flex;flex-direction:column;gap:18px">'
             + "".join(f'<p style="font-size:26px;line-height:1.35;color:{INK}">{r}</p>' for r in refs) + "</div>")
slides.append(("references", content("references", 19, "Conclusions", "References", refs_html,
    "Key references; the full list is in the research guide and literature review.", panel_style="display:flex;align-items:start")))

slides.append(("thanks", content("thanks", 20, None, "Questions?", bullets([
    ("Interactive demo of the arousal monitor", ["claude.ai/artifact/M3MtScwGda3GP4d2e27dUU"]),
    ("Full write-ups", ["Interpretability report, external validation report, 19-page research guide"]),
    ("Code", ["app/arousal_monitor and scripts/ in the project repository"]),
]), "Thank you.", panel_style="display:flex;align-items:center")))

for sid, html in slides:
    with open(os.path.join(OUT, "slides", f"{sid}.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

deck = {"v": 4, "createdOnFiles": {"v": 1, "at": "2026-10-18T00:50:00Z"}, "lists": "css",
        "title": "What EEG-to-BOLD Models Actually Learn",
        "order": [s for s, _ in slides],
        "sections": {"s1": {"description": "Title, overview, background, motivation and research questions", "start": "title"},
                     "s2": {"description": "Research methods", "start": "methods"},
                     "s3": {"description": "Results", "start": "res_real"},
                     "s4": {"description": "Application: the EEG arousal monitor", "start": "application"},
                     "s5": {"description": "Findings, implications, further research, references and questions", "start": "findings"}},
        "faces": {}, "designSystems": []}
with open(os.path.join(OUT, "deck.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(deck, f, indent=2, ensure_ascii=False)
print(len(slides), "slides:", ", ".join(s for s, _ in slides))
