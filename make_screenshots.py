"""Render real command output as terminal-style screenshots for the report.

Run:  python make_screenshots.py     (needs playwright + chromium)
"""
import html
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
OUT = ROOT / "results" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def run(cmd: str) -> str:
    r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True)
    return (r.stdout + r.stderr).rstrip()


def tree() -> str:
    lines = []
    keep = ["smartcity", "data", "tests", "results", "README.md", "app.py", "benchmark.py",
            "make_figures.py", "make_report.py", "make_screenshots.py", "requirements.txt"]
    for k in keep:
        p = ROOT / k
        if p.is_dir():
            lines.append(f"{k}/")
            for c in sorted(p.iterdir()):
                if c.name.startswith(("__", ".")) or c.is_dir():
                    continue
                lines.append(f"    {c.name}")
        elif p.exists():
            lines.append(k)
    return "\n".join(lines)


SHOTS = {
    "shot1_structure.png": ("$ tree smart-city-traffic", tree()),
    "shot2_data.png": ("$ head data/nodes.csv data/edges.csv",
                       run("head -6 data/nodes.csv; echo; head -6 data/edges.csv; echo; "
                           "echo \"nodes: $(($(wc -l < data/nodes.csv)-1))   "
                           "edges: $(($(wc -l < data/edges.csv)-1))\"")),
    "shot3_tests.png": ("$ python -m pytest -v", run(
        "python -m pytest -v 2>&1 | grep -v '^$' | sed -e 's#tests/test_algorithms.py::##' "
        "| cut -c1-110")),
    "shot4_benchmark.png": ("$ python benchmark.py   # results/benchmark.csv", run(
        "python -c \"import csv;r=list(csv.reader(open('results/benchmark.csv')));"
        "w=[max(len(x[i]) for x in r)+2 for i in range(len(r[0]))];"
        "print('\\n'.join(''.join(c.rjust(w[i]) for i,c in enumerate(x)) for x in r))\"")),
    "shot5_analysis.png": ("$ cat results/run_log.txt", run("fold -s -w 105 results/run_log.txt")),
}


def page(cmd, body):
    return f"""<html><body style="margin:0;background:#1e1e2e">
<div style="width:1000px;padding:0;font-family:'DejaVu Sans Mono',monospace;font-size:14px">
<div style="background:#313244;padding:8px 14px;color:#cdd6f4;font-size:13px">
<span style="color:#f38ba8">●</span> <span style="color:#f9e2af">●</span>
<span style="color:#a6e3a1">●</span>&nbsp;&nbsp;Terminal - smart-city-traffic</div>
<pre style="margin:0;padding:14px;color:#cdd6f4;white-space:pre-wrap;line-height:1.35">
<span style="color:#a6e3a1">{html.escape(cmd)}</span>
{html.escape(body)}</pre></div></body></html>"""


with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1000, "height": 200}, device_scale_factor=2)
    for name, (cmd, body) in SHOTS.items():
        pg.set_content(page(cmd, body))
        pg.screenshot(path=str(OUT / name), full_page=True)
        print("saved", name)
    b.close()
