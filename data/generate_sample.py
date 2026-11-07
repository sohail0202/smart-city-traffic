"""Generate a reproducible synthetic city: a 12x10 grid with ring road and arterials.

Run:  python data/generate_sample.py
Writes data/nodes.csv and data/edges.csv
"""
import csv
import random
from pathlib import Path

random.seed(42)
OUT = Path(__file__).parent
COLS, ROWS, SPACING = 12, 10, 0.8      # km between neighbouring intersections

AREAS = ["Central", "Market", "Airport Rd", "University", "Harbour", "Tech Park",
         "Old Town", "Stadium", "Hospital", "Station", "Lakeside", "Industrial"]


def nid(c, r):
    return r * COLS + c


nodes = []
for r in range(ROWS):
    for c in range(COLS):
        name = f"{AREAS[(c + 3 * r) % len(AREAS)]} {c}-{r}"
        nodes.append((nid(c, r), name,
                      round(c * SPACING + random.uniform(-0.15, 0.15), 3),
                      round(r * SPACING + random.uniform(-0.15, 0.15), 3)))

pos = {n[0]: (n[2], n[3]) for n in nodes}
edges = []


def add(a, b, speed, base_cong):
    (x1, y1), (x2, y2) = pos[a], pos[b]
    length = round(((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5, 3)
    cong = round(min(1.0, max(0.0, random.gauss(base_cong, 0.12))), 2)
    edges.append((a, b, length, speed, cong))


for r in range(ROWS):
    for c in range(COLS):
        arterial = r in (3, 6) or c in (3, 8)          # fast, busier roads
        speed, base = (60, 0.55) if arterial else (40, 0.25)
        if c + 1 < COLS and random.random() > 0.08:    # a few missing links
            add(nid(c, r), nid(c + 1, r), speed, base)
        if r + 1 < ROWS and random.random() > 0.08:
            add(nid(c, r), nid(c, r + 1), speed, base)
        # occasional diagonal shortcut
        if c + 1 < COLS and r + 1 < ROWS and random.random() < 0.10:
            add(nid(c, r), nid(c + 1, r + 1), 50, 0.3)

# make sure the network is connected: link any orphan to its left/upper neighbour
deg = {n[0]: 0 for n in nodes}
for a, b, *_ in edges:
    deg[a] += 1
    deg[b] += 1
for (n, *_), d in zip(nodes, deg.values()):
    if d == 0:
        c, r = n % COLS, n // COLS
        add(n, nid(c - 1, r) if c else nid(c, r - 1), 40, 0.25)

with open(OUT / "nodes.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "name", "x", "y"])
    w.writerows(nodes)
with open(OUT / "edges.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["u", "v", "length_km", "speed_kmh", "congestion"])
    w.writerows(edges)

print(f"wrote {len(nodes)} nodes and {len(edges)} edges to {OUT}")
