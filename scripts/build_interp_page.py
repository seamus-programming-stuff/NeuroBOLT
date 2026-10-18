#!/usr/bin/env python3
"""Build the interpretability web page (reports/interpretability/index.html) from its markdown report.

    python scripts/build_interp_page.py

Uses the hypothesis page's styles and markdown subset (### headings, - bullets, pipe tables, images,
paragraphs, **bold**, `code`, links); each "## " heading of the report becomes a section. Figures are
referenced by file name, so publish the page with every PNG in reports/interpretability/ beside it.
"""
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_hypotheses_report import inline, markdown_to_html  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(REPO, "reports", "NeuroBOLT interpretability.md")
STYLE_SOURCE = os.path.join(REPO, "reports", "hypotheses", "template.html")
OUT = os.path.join(REPO, "reports", "interpretability", "index.html")


def main():
    text = open(REPORT, encoding="utf-8").read()
    head = open(STYLE_SOURCE, encoding="utf-8").read().split("<main", 1)[0]
    head = head.replace("<title>NeuroBOLT Hypothesis Tests</title>", "<title>NeuroBOLT Interpretability</title>")
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip()
    byline_end = next(i for i, line in enumerate(lines) if line.startswith("## "))
    intro = "\n".join(lines[1:byline_end]).strip().split("\n\n")
    byline, standfirst = intro[0], "\n\n".join(intro[1:])
    sections = re.split(r"^## ", "\n".join(lines[byline_end:]), flags=re.M)[1:]
    body = []
    for i, section in enumerate(sections):
        heading, _, content = section.partition("\n")
        anchor = f"s{i + 1}"
        body.append(f'  <section class="col" aria-labelledby="{anchor}">\n    <h2 id="{anchor}">{inline(heading.strip())}</h2>\n'
                    f"    {markdown_to_html(content)}\n  </section>")
    page = (head + '<main class="page">\n  <header class="col">\n'
            '    <span class="eyebrow">Interpretability round · cross-subject EEG-to-BOLD</span>\n'
            f"    <h1>{html.escape(title)}</h1>\n"
            f'    <p class="status">{inline(byline)}</p>\n'
            f"    {markdown_to_html(standfirst)}\n  </header>\n" + "\n".join(body) +
            '\n  <footer class="col note">Companion pages: <a href="https://claude.ai/artifact/MAxjxrsN8EjVAkRN6kWrXV">'
            'NeuroBOLT Hypothesis Tests</a> and <a href="https://claude.ai/artifact/SZerzG3z2x4vUbJebDe2Di">NeuroBOLT '
            'Reproduction</a>. Code: <code>scripts/interp_*.py</code> and <code>reports/NeuroBOLT interpretability.md</code> '
            "in the project repository.</footer>\n</main>\n")
    with open(OUT, "w", encoding="utf-8") as stream:
        stream.write(page)
    print(f"Wrote {OUT} ({len(sections)} sections)")


if __name__ == "__main__":
    main()
