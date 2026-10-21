#!/usr/bin/env python3
"""Build a one-page A0 research poster, following the supplied poster examples.

Dependencies: numpy, pandas, reportlab. All chart marks and text are vector PDF
objects. Run from any directory; paths are resolved relative to this repository.
The poster does not submit experiments or change the underlying research reports.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A0
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
W, H = A0
MARGIN = 85.0
GUTTER = 62.0
COL = (W - 2 * MARGIN - GUTTER) / 2
LEFT = MARGIN
RIGHT = MARGIN + COL + GUTTER
BLUE = "#0074B8"
ORANGE = "#C87016"
INK = "#192D3C"
MUTED = "#52616D"
GRID = "#DAE2E7"
LIGHT_BLUE = "#EFF6FA"
LIGHT_ORANGE = "#FBF4E9"
GRAY = "#77828C"
REPO_URL = "https://github.com/seamus-programming-stuff/NeuroBOLT"

ROI7 = [
    "Cuneus", "Heschl’s gyrus", "Middle frontal gyrus anterior",
    "Precuneus anterior", "Putamen", "Thalamus", "global signal clean",
]
# Student-t 97.5th percentiles; the poster's inferential units are 22 or 28 people.
T975 = {22: 2.079613844727662, 28: 2.0518305164802833}


def interval(values):
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    n = len(a)
    if n not in T975:
        raise ValueError(f"Unexpected person count for a poster confidence interval: {n}")
    m = float(a.mean())
    h = T975[n] * float(a.std(ddof=1)) / math.sqrt(n)
    return {"mean": m, "low": m - h, "high": m + h, "n": n}


def read_data():
    cv = pd.read_csv(ROOT / "reports/interpretability/data/cv_scores.csv")
    cv["person"] = cv["scan"].str.extract(r"(sub\d+)")
    vu = {}
    for key in ("eeg_full", "bands60", "vigilance"):
        rows = cv[(cv["features"] == key) & (cv["targets"] == "all65") & cv["roi"].isin(ROI7)]
        vu[key] = interval(rows.groupby("person")["corr"].mean())
    # The NeuroBOLT CV predictions are retained on M3; these values and paired
    # statistics are transcribed from the checked-in, subject-grouped CV table.
    vu["neurobolt24"] = {"mean": .336, "low": .266, "high": .405, "n": 22}

    gsr = {}
    for name in ("all65", "gsr64"):
        rows = cv[(cv["features"] == "eeg_full") & (cv["targets"] == name) &
                  (cv["roi"] != "global signal clean")]
        assert rows["roi"].nunique() == 64
        gsr[name] = interval(rows.groupby("person")["corr"].mean())

    tr = pd.read_csv(ROOT / "reports/external/data/transfer.csv")
    rows = tr[(tr["model"] == "full") & (tr["targets"] == "all65") & tr["roi"].isin(ROI7)]
    people = rows.groupby(["protocol", "condition", "subject"])["corr"].mean()
    transfer = {}
    for protocol in ("zero-shot", "in-domain"):
        for condition in ("EC", "EO"):
            transfer[f"{protocol}_{condition}"] = interval(people.loc[(protocol, condition)])
    transfer["paired_local_minus_frozen_EC"] = interval(
        people.loc[("in-domain", "EC")] - people.loc[("zero-shot", "EC")])

    monitor = pd.read_csv(ROOT / "reports/external/data/monitor_runs.csv")
    assert len(monitor) == 56 and monitor["subject"].nunique() == 28
    replay = {
        condition: interval(monitor[monitor["condition"] == condition].groupby("subject")["r_streaming"].mean())
        for condition in ("EC", "EO")
    }
    replay["median_latency_ms"] = float(monitor["latency_ms_median"].median())
    demo = json.loads((ROOT / "reports/external/data/demo.json").read_text(encoding="utf-8"))
    ec_runs = monitor[monitor["condition"] == "EC"].set_index("run")
    # Select the run closest to the median offline tracking accuracy, rather than
    # showing the best run. The selection rule is stated in the visible caption.
    median = float(ec_runs["r_offline"].median())
    run = min(ec_runs.index, key=lambda k: abs(float(ec_runs.loc[k, "r_offline"]) - median))
    example = {"run": run, "r": float(ec_runs.loc[run, "r_offline"]), **demo[run]}

    maps = np.load(ROOT / "reports/interpretability/data/maps.npz")
    labels = [str(x) for x in maps["labels"]]
    # band_coupling: (classic band, lag, target), Fisher-z mean over scans.
    band = maps["band_coupling"]
    if band.shape != (5, 12, 65):
        raise ValueError(f"Unexpected coupling tensor: {band.shape}")
    coupling = {
        "lag": maps["lag_centres"].tolist(),
        "global": band[2, :, labels.index("global signal clean")].tolist(),
        "thalamus": band[2, :, labels.index("Thalamus")].tolist(),
    }
    return {"vu": vu, "gsr": gsr, "transfer": transfer, "replay": replay,
            "example": example, "coupling": coupling}


def register_fonts():
    fonts = Path("C:/Windows/Fonts")
    for name, file in (("Poster", "arial.ttf"), ("Poster-Bold", "arialbd.ttf"),
                       ("Poster-Italic", "ariali.ttf"), ("Poster-BoldItalic", "arialbi.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(fonts / file)))
    pdfmetrics.registerFontFamily("Poster", normal="Poster", bold="Poster-Bold",
                                  italic="Poster-Italic", boldItalic="Poster-BoldItalic")


class Poster:
    def __init__(self, path):
        self.c = Canvas(str(path), pagesize=A0, pageCompression=1)
        self.c.setTitle("Interpretable EEG-to-fMRI prediction across people and recording sites")
        self.c.setAuthor("Seamus Taylor")
        self.c.setCreator("NeuroBOLT research poster / ReportLab")
        self.c.setSubject("Research poster: linear baselines, interpretation, external validation and an EEG arousal monitor")
        self.text_boxes = []

    def rect(self, x, y, w, h, fill=None, stroke=None, lw=2):
        c = self.c
        if fill:
            c.setFillColor(colors.HexColor(fill))
        if stroke:
            c.setStrokeColor(colors.HexColor(stroke))
        c.setLineWidth(lw)
        c.rect(x, H - y - h, w, h, stroke=int(bool(stroke)), fill=int(bool(fill)))

    def line(self, x1, y1, x2, y2, color=GRID, lw=2):
        self.c.setStrokeColor(colors.HexColor(color))
        self.c.setLineWidth(lw)
        self.c.line(x1, H - y1, x2, H - y2)

    def text(self, value, x, y, size=35, bold=False, color=INK, align="left"):
        """Position by the top of the font's em box, in poster points."""
        self.c.setFillColor(colors.HexColor(color))
        self.c.setFont("Poster-Bold" if bold else "Poster", size)
        baseline = H - y - size * .82
        if align == "right":
            self.c.drawRightString(x, baseline, value)
        elif align == "center":
            self.c.drawCentredString(x, baseline, value)
        else:
            self.c.drawString(x, baseline, value)

    def para(self, value, x, y, w, size=35, leading=None, color=INK, bold=False, max_h=None):
        style = ParagraphStyle(
            "poster", fontName="Poster-Bold" if bold else "Poster", fontSize=size,
            leading=leading or size * 1.29, textColor=colors.HexColor(color),
            alignment=TA_LEFT, spaceBefore=0, spaceAfter=0,
        )
        p = Paragraph(value, style)
        _, h = p.wrap(w, H)
        if max_h is not None and h > max_h + .01:
            raise ValueError(f"Text overflow ({h:.1f} > {max_h:.1f} pt): {value[:90]}")
        if x < 0 or y < 0 or x + w > W + .1 or y + h > H + .1:
            raise ValueError(f"Text outside poster: {value[:80]}")
        p.drawOn(self.c, x, H - y - h)
        self.text_boxes.append({"x": x, "y": y, "w": w, "h": h,
                                "text": value, "font_size": size})
        return h

    def heading(self, title, x, y, w=COL, number=None):
        if number is not None:
            title = f"{number}. {title}"
        return self.para(title, x, y, w, size=47, leading=56, bold=True,
                         color=BLUE, max_h=58)

    def marker(self, x, y, color, square=False, hollow=False, radius=10):
        self.c.setStrokeColor(colors.HexColor(color))
        self.c.setFillColor(colors.white if hollow else colors.HexColor(color))
        self.c.setLineWidth(3)
        if square:
            self.c.rect(x - radius, H - y - radius, 2 * radius, 2 * radius, fill=1, stroke=1)
        else:
            self.c.circle(x, H - y, radius, fill=1, stroke=1)

    def forest(self, x, top, entries, axis_max=.5):
        """Directly labelled scientific dot chart; all intervals are over people."""
        label_w, plot_w = 352, COL - 475
        px, py = x + label_w, top
        axis_y = top + 334
        scale = lambda r: px + plot_w * r / axis_max
        for tick in np.arange(0, axis_max + .001, .1):
            xx = scale(tick)
            self.line(xx, top + 8, xx, axis_y, GRID, 1.6)
            self.text(f"{tick:.1f}", xx, axis_y + 15, size=27, color=MUTED, align="center")
        for i, row in enumerate(entries):
            yy = py + 43 + 77 * i
            self.text(row["label"], x, yy - 17, size=33, bold=row.get("bold", False))
            d = row["data"]
            self.line(scale(d["low"]), yy, scale(d["high"]), yy, row["color"], 5)
            for v in (d["low"], d["high"]):
                self.line(scale(v), yy - 9, scale(v), yy + 9, row["color"], 3)
            self.marker(scale(d["mean"]), yy, row["color"], square=row.get("square", False),
                        hollow=row.get("hollow", False))
            self.text(f'{d["mean"]:.3f}', x + COL, yy - 20, size=39,
                      bold=True, color=row["color"], align="right")
        self.line(px, axis_y, px + plot_w, axis_y, MUTED, 2)
        self.text("Mean test R (95% CI)", px + plot_w / 2, axis_y + 56,
                  size=29, color=MUTED, align="center")

    def plot(self, x, y, w, h, xlim, ylim, xticks, yticks, xlabel, ylabel, series):
        # x/y include the axis labels; plot area retains generous readable margins.
        px, py = x + 87, y + 25
        pw, ph = w - 112, h - 130
        sx = lambda v: px + pw * (v - xlim[0]) / (xlim[1] - xlim[0])
        sy = lambda v: py + ph * (1 - (v - ylim[0]) / (ylim[1] - ylim[0]))
        for v in yticks:
            self.line(px, sy(v), px + pw, sy(v), GRID, 1.7)
            self.text(f"{v:g}", px - 16, sy(v) - 12, size=26, align="right", color=MUTED)
        if ylim[0] < 0 < ylim[1]:
            self.line(px, sy(0), px + pw, sy(0), "#B9C7D0", 2)
        for v in xticks:
            self.line(sx(v), py + ph, sx(v), py + ph + 9, MUTED, 1.8)
            self.text(f"{v:g}", sx(v), py + ph + 17, size=27, align="center", color=MUTED)
        self.line(px, py, px, py + ph, MUTED, 2)
        self.line(px, py + ph, px + pw, py + ph, MUTED, 2)
        self.text(xlabel, px + pw / 2, py + ph + 60, size=29, align="center", color=MUTED)
        self.c.saveState()
        self.c.translate(x + 19, H - (py + ph / 2))
        self.c.rotate(90)
        self.c.setFont("Poster", 29)
        self.c.setFillColor(colors.HexColor(MUTED))
        self.c.drawCentredString(0, 0, ylabel)
        self.c.restoreState()
        self.c.saveState()
        clip = self.c.beginPath()
        clip.rect(px, H - py - ph, pw, ph)
        self.c.clipPath(clip, stroke=0, fill=0)
        for item in series:
            self.c.setStrokeColor(colors.HexColor(item["color"]))
            self.c.setLineWidth(item.get("lw", 4))
            self.c.setDash(12, 7) if item.get("dash") else self.c.setDash()
            p = self.c.beginPath()
            for i, (xx, yy) in enumerate(zip(item["x"], item["y"])):
                if i == 0 or (item.get("gap") is not None and
                              abs(xx - item["x"][i - 1]) > item["gap"]):
                    p.moveTo(sx(xx), H - sy(yy))
                else:
                    p.lineTo(sx(xx), H - sy(yy))
            self.c.drawPath(p)
        self.c.restoreState()

    def legend(self, x, y, items, step):
        for i, (label, color, dash) in enumerate(items):
            xx = x + step * i
            self.c.setDash(11, 7) if dash else self.c.setDash()
            self.line(xx, y + 16, xx + 55, y + 16, color, 5)
            self.c.setDash()
            self.text(label, xx + 69, y, size=29, color=MUTED)

    def finish(self):
        self.c.showPage()
        self.c.save()


def build_poster(path, d):
    p = Poster(path)
    p.rect(0, 0, W, H, fill="#FFFFFF")
    p.rect(MARGIN - 22, 68, W - 2 * MARGIN + 44, 318, fill=BLUE)
    p.para("Interpretable EEG-to-fMRI prediction", MARGIN + 25, 105,
           W - 2 * MARGIN - 50, size=99, leading=112, bold=True, color="#FFFFFF", max_h=118)
    p.para("across people and recording sites", MARGIN + 25, 222,
           W - 2 * MARGIN - 50, size=93, leading=106, bold=True, color="#FFFFFF", max_h=115)
    p.text("Seamus Taylor", LEFT, 421, size=42, bold=True)
    p.text("Analysis on Monash MASSIVE M3  |  October 2026", W - MARGIN, 431,
           size=29, color=MUTED, align="right")
    p.para("Lagged EEG power outperforms NeuroBOLT and supports an arousal-monitor prototype.",
           LEFT, 491, W - 2 * MARGIN, size=42, leading=52, max_h=56)

    # Two opening sections match the background/methodology structure in the examples.
    for x in (LEFT, RIGHT):
        p.rect(x - 16, 584, COL + 32, 464, stroke="#B6D9EC", lw=2)
    p.heading("Background and research question", LEFT + 10, 606, COL - 20)
    p.para("EEG measures electrical activity at the scalp; fMRI BOLD reflects slower changes in blood oxygenation. "
           "Predicting BOLD from EEG could help monitor fluctuations in brain state.",
           LEFT + 10, 684, COL - 20, size=35, leading=46, max_h=150)
    p.para("NeuroBOLT [1] combines spectral features with a pretrained transformer. Can an interpretable EEG model "
           "predict unseen people and generalise across sites?",
           LEFT + 10, 854, COL - 20, size=35, leading=46, max_h=160)

    p.heading("Methodology", RIGHT + 10, 606, COL - 20)
    p.para("<b>VU:</b> 22 people, 29 eyes-closed scans (~20 min).<br/>"
           "<b>External ds006040 [2]:</b> 28 people, 56 runs (~6 min), eyes closed and open; a different scanner and EEG cap.",
           RIGHT + 10, 682, COL - 20, size=33, leading=43, max_h=140)
    # This small data-processing diagram is an explanatory figure, not decoration.
    widths = [293, 293, 350]
    texts = [("1 Hz log power", "26 channels / 1-45 Hz"),
             ("24 s history", "12 lags of 2 s"),
             ("Ridge regression", "Regional + global BOLD")]
    xx = RIGHT + 10
    for i, (width, (title, subtitle)) in enumerate(zip(widths, texts)):
        p.rect(xx, 838, width, 98, fill=LIGHT_BLUE)
        p.text(title, xx + width / 2, 853, size=30, bold=True, color=BLUE, align="center")
        p.text(subtitle, xx + width / 2, 893, size=25, color=MUTED, align="center")
        if i < 2:
            p.text("→", xx + width + 18, 864, size=37, color=BLUE, align="center")
        xx += width + 39
    p.para("Five folds grouped by person; separate validation people for tuning. Frozen-model test at the new site. "
           "Mean <i>R</i> and 95% CIs over people.",
           RIGHT + 10, 953, COL - 20, size=31, leading=39, max_h=78)

    p.rect(MARGIN - 22, 1068, W - 2 * MARGIN + 44, 83, fill=ORANGE)
    p.text("Results", LEFT + 10, 1085, size=54, bold=True, color="#FFFFFF")
    p.text("Prediction, interpretation and an independent-site application", RIGHT + COL, 1097,
           size=34, color="#FFFFFF", align="right")

    p.heading("Prediction in unseen people", LEFT, 1194, number=1)
    p.text("VU cohort  |  7 targets  |  22 held-out people", LEFT, 1264, size=29, color=MUTED)
    p.forest(LEFT, 1309, [
        {"label": "Ridge: 1 Hz bins", "data": d["vu"]["eeg_full"], "color": ORANGE, "bold": True},
        {"label": "Five band powers", "data": d["vu"]["bands60"], "color": ORANGE, "hollow": True},
        {"label": "NeuroBOLT (24 s)", "data": d["vu"]["neurobolt24"], "color": BLUE, "square": True},
        {"label": "Vigilance index", "data": d["vu"]["vigilance"], "color": GRAY},
    ])
    p.para("Ridge led NeuroBOLT in <b>19/22 people</b>:<br/>"
           "ΔR = +0.045 (95% CI +0.023 to +0.067).",
           LEFT, 1738, COL, size=35, leading=46, max_h=95)
    p.para("Seven targets: six DiFuMo regions + global BOLD. NeuroBOLT: shared 24 s model, three seeds. "
           "Vigilance index: alpha/(delta + theta) power.",
           LEFT, 1850, COL, size=27, leading=34, color=MUTED, max_h=70)

    p.heading("Transfer to an independent site", RIGHT, 1194, number=2)
    p.text("ds006040  |  7 targets  |  28 new people", RIGHT, 1264, size=29, color=MUTED)
    p.forest(RIGHT, 1309, [
        {"label": "Closed: frozen VU", "data": d["transfer"]["zero-shot_EC"], "color": ORANGE, "bold": True},
        {"label": "Closed: within site", "data": d["transfer"]["in-domain_EC"], "color": BLUE, "square": True},
        {"label": "Open: frozen VU", "data": d["transfer"]["zero-shot_EO"], "color": ORANGE},
        {"label": "Open: within site", "data": d["transfer"]["in-domain_EO"], "color": BLUE, "square": True},
    ])
    p.para("Eyes closed: similar means for frozen and local models. Paired ΔR (local - frozen) = +0.001 "
           "(95% CI -0.017 to +0.020).",
           RIGHT, 1738, COL, size=35, leading=46, max_h=140)
    p.para("Published NeuroBOLT reached R = 0.180 with eyes closed. Eyes-open rest was harder for the frozen ridge model.",
           RIGHT, 1887, COL, size=27, leading=34, color=MUTED, max_h=70)

    p.line(LEFT, 1976, W - MARGIN, 1976, GRID, 2)
    p.heading("What carries the prediction?", LEFT, 2012, number=3)
    p.heading("Prototype: EEG arousal monitor", RIGHT, 2012, number=4)

    p.text("0.343  →  0.144", LEFT, 2092, size=69, bold=True, color=ORANGE)
    p.para("Mean R across the same 64 regions, before and after global-signal regression (GSR).",
           LEFT, 2181, COL, size=31, leading=39, max_h=81)
    p.legend(LEFT + 95, 2294, [("Global BOLD", ORANGE, False), ("Thalamus", BLUE, True)], step=468)
    coup = d["coupling"]
    p.plot(LEFT, 2336, COL, 316, (24, 0), (-.3, .3), [24, 16, 8, 0], [-.3, 0, .3],
           "Seconds before the BOLD frame", "Alpha-BOLD r", [
               {"x": coup["lag"], "y": coup["global"], "color": ORANGE, "lw": 5},
               {"x": coup["lag"], "y": coup["thalamus"], "color": BLUE, "lw": 5, "dash": True},
           ])
    p.para("Alpha power couples negatively with global BOLD around 9 s earlier; the thalamus has a positive "
           "component around 3 s. This supports a brain-state interpretation, with regional differences.",
           LEFT, 2670, COL, size=34, leading=44, max_h=176)

    ex = d["example"]
    pp = np.asarray(ex["pred_global"], dtype=float)
    yy = np.asarray(ex["measured_global"], dtype=float)
    # Standardise only for plotting both time courses on a common y axis.
    pp = (pp - pp.mean()) / pp.std()
    yy = (yy - yy.mean()) / yy.std()
    p.legend(RIGHT + 90, 2112, [("Measured fMRI", GRAY, False), ("EEG estimate", ORANGE, False)], step=510)
    p.plot(RIGHT, 2156, COL, 378, (0, 400), (-3, 3), [0, 100, 200, 300, 400], [-2, 0, 2],
           "Time in recording (s)", "Global BOLD (z)", [
               {"x": ex["t"], "y": yy.tolist(), "color": GRAY, "lw": 3.5, "gap": 4.1},
               {"x": ex["t"], "y": pp.tolist(), "color": ORANGE, "lw": 4.5, "gap": 4.1},
           ])
    p.para(f'Example: {escape(ex["run"])} (r = {ex["r"]:.2f}), closest to median eyes-closed accuracy. '
           'Gap = excluded EEG windows.',
           RIGHT, 2547, COL, size=27, leading=34, color=MUTED, max_h=70)
    p.text("r = 0.263", RIGHT, 2650, size=62, bold=True, color=ORANGE)
    p.text("~3 ms / volume", RIGHT + COL, 2650, size=53, bold=True, color=BLUE, align="right")
    p.para("Streaming replay: 28 eyes-closed runs.<br/>"
           "95% CI 0.205 to 0.321; one CPU core.<br/>"
           "EEG estimates global BOLD; fMRI assesses accuracy.",
           RIGHT, 2735, COL, size=32, leading=41, max_h=126)

    # Close with evaluation and further research, as in the reference posters.
    row_y = 2910
    p.rect(LEFT - 16, row_y, COL + 32, 275, fill=LIGHT_BLUE)
    p.rect(RIGHT - 16, row_y, COL + 32, 275, fill=LIGHT_ORANGE)
    p.heading("Conclusion", LEFT + 12, row_y + 19, COL - 24)
    p.para("Penalised linear models provide a strong baseline for EEG-to-BOLD prediction. "
           "Much of the predictable signal follows brain-wide state fluctuations. "
           "Transfer worked on one independent site; the model supports an arousal-monitor prototype.",
           LEFT + 12, row_y + 94, COL - 24, size=34, leading=44, max_h=176)
    p.heading("Limitations and further research", RIGHT + 12, row_y + 19, COL - 24)
    p.para("Test region-specific prediction with respiration and motion controls at more sites. "
           "Validate arousal flags against pupil measurements or sleep staging. "
           "These are observational results; streaming used replayed, cleaned EEG. Prospective use remains untested.",
           RIGHT + 12, row_y + 94, COL - 24, size=34, leading=44, max_h=176)

    footer = 3205
    p.text("References and resources", LEFT, footer, size=31, bold=True, color=BLUE)
    p.para("<b>[1]</b> Li et al. NeuroBOLT: Resting-state EEG-to-fMRI synthesis with multi-dimensional feature mapping. NeurIPS, 2024.<br/>"
           "<b>[2]</b> Cha et al. Sustained attention task (gradCPT) dataset using simultaneous EEG-fMRI and DTI. Scientific Data, 2026. "
           "doi:10.1038/s41597-026-06616-6. OpenNeuro: ds006040.<br/>"
           "Analysis code, model weights and full reports: github.com/seamus-programming-stuff/NeuroBOLT",
           LEFT, footer + 44, W - 2 * MARGIN - 244, size=22, leading=28, max_h=100)
    qr = QrCodeWidget(REPO_URL, barLevel="M")
    x0, y0, x1, y1 = qr.getBounds()
    size = 125
    drawing = Drawing(size, size, transform=[size / (x1 - x0), 0, 0, size / (y1 - y0), 0, 0])
    drawing.add(qr)
    qr_x, qr_y = W - MARGIN - 170, footer - 12
    renderPDF.draw(drawing, p.c, qr_x, H - qr_y - size)
    p.c.linkURL(REPO_URL, (qr_x, H - qr_y - size, qr_x + size, H - qr_y), relative=0)
    p.text("Code + reports", qr_x + size / 2, footer + 117, size=21, color=MUTED, align="center")
    p.finish()
    return p.text_boxes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "output/pdf/NeuroBOLT_research_poster_A0.pdf")
    parser.add_argument("--metadata", type=Path, default=ROOT / "reports/poster/poster_data.json")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    register_fonts()
    data = read_data()
    layout = build_poster(args.out, data)
    data["sources"] = [
        "reports/NeuroBOLT hypothesis tests.md", "reports/NeuroBOLT interpretability.md",
        "reports/NeuroBOLT external validation.md", "reports/interpretability/data/cv_scores.csv",
        "reports/interpretability/data/maps.npz", "reports/external/data/transfer.csv",
        "reports/external/data/monitor_runs.csv", "reports/external/data/demo.json",
    ]
    data["layout_text_boxes"] = layout
    args.metadata.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Poster: {args.out}")
    print(f"Size: {W / 72 * 25.4:.0f} x {H / 72 * 25.4:.0f} mm (A0 portrait)")
    print(f"Representative trace: {data['example']['run']}, r = {data['example']['r']:.3f}")
    print(f"Data and text layout: {args.metadata}")


if __name__ == "__main__":
    main()
