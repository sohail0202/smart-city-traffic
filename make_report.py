"""Build Capstone_Report.docx from the project's real results.

Run:  python make_report.py   (after benchmark.py and make_figures.py)
Edit NAME / ROLL / COURSE below before running.
"""
import csv
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

NAME = "Vansh"
ROLL = "2401201123"
COURSE = "BCA (AI & DS)"
REPO = ""   # paste your GitHub link here after you create the repo, e.g. https://github.com/you/smart-city-traffic

ROOT = Path(__file__).parent
RES = ROOT / "results"
log = (RES / "run_log.txt").read_text().strip().splitlines()
bench = list(csv.DictReader(open(RES / "benchmark.csv")))

d = Document()
st = d.styles["Normal"]
st.font.name, st.font.size = "Calibri", Pt(11)


def h(text, lvl=1):
    d.add_heading(text, lvl)


def p(text):
    d.add_paragraph(text)


def bullets(items):
    for i in items:
        d.add_paragraph(i, style="List Bullet")


def table(header, rows):
    t = d.add_table(rows=1, cols=len(header))
    t.style = "Light Grid Accent 1"
    for c, txt in zip(t.rows[0].cells, header):
        c.text = txt
    for r in rows:
        cells = t.add_row().cells
        for c, txt in zip(cells, r):
            c.text = str(txt)
    d.add_paragraph()


def fig(name, caption, w=5.8):
    d.add_picture(str(RES / name), width=Inches(w))
    d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = d.add_paragraph(caption)
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.runs[0].italic = True


# ------------------------------------------------------------------ title
t = d.add_heading("Smart City Traffic Management and Route Optimization System", 0)
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
for line in ("Capstone Project Report", f"{NAME}  |  Roll No. {ROLL}", COURSE,
             *([f"Repository: {REPO}"] if REPO else [])):
    para = d.add_paragraph(line)
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
d.add_page_break()

# ---------------------------------------------------------------- 1 problem
h("1. Problem Statement")
p("Urban roads suffer from congestion, incidents and poorly planned infrastructure. "
  "Commuters need fast and reliable routes, and city administrators need to know which "
  "roads and intersections matter most. This project models a city's transportation "
  "network as a graph and applies graph traversal, shortest-path and minimum spanning "
  "tree algorithms to support routing, traffic evaluation and infrastructure planning.")
h("Objectives", 2)
bullets([
    "Represent intersections as nodes and roads as weighted edges (distance or congestion-adjusted travel time).",
    "Implement BFS, DFS, Dijkstra, A*, Kruskal and Prim from scratch and verify them against each other.",
    "Provide commuter features: fastest route, shortest route, alternative route, incident re-routing.",
    "Provide administrator features: congestion hotspots, critical intersections and roads, backbone planning.",
    "Provide an interactive dashboard and a measured performance analysis.",
])

# ----------------------------------------------------------------- 2 design
h("2. System Design")
h("2.1 Graph model", 2)
p("The network is an undirected weighted graph G = (V, E) stored as an adjacency list. "
  "Each road stores length (km), speed limit (km/h) and a congestion level in [0, 1]. "
  "Travel time in minutes is free-flow time multiplied by (1 + 2c^2), where c is "
  "congestion, so a fully jammed road takes three times as long as an empty one. "
  "Users can switch the optimisation metric between distance and time.")
h("2.2 Architecture", 2)
table(["Layer", "Module", "Responsibility"], [
    ["Data", "data/*.csv, generate_sample.py", "Reproducible synthetic city (seed 42)"],
    ["Model", "smartcity/graph.py", "Graph, edges, congestion updates, road closure, CSV loading"],
    ["Algorithms", "smartcity/algorithms.py", "Traversal, shortest path, MST, network analysis"],
    ["Visualisation", "smartcity/viz.py", "Congestion maps, routes, MST, heat map, benchmark charts"],
    ["Interface", "app.py (Streamlit)", "Four-tab interactive dashboard"],
    ["Evaluation", "tests/, benchmark.py, make_figures.py", "Correctness tests and performance study"],
])
h("2.3 Algorithm selection", 2)
table(["Algorithm", "Complexity", "Purpose"], [
    ["BFS / DFS", "O(V+E)", "Reachability, hop distance, connected components"],
    ["Dijkstra (binary heap)", "O((V+E) log V)", "Fastest or shortest route; single-source costs"],
    ["A*", "O((V+E) log V) worst case", "Faster point-to-point routing with a straight-line heuristic"],
    ["Kruskal (union-find)", "O(E log E)", "Minimum spanning tree: cheapest connected backbone"],
    ["Prim (heap)", "O(E log V)", "MST, used to cross-check Kruskal"],
    ["Tarjan low-link", "O(V+E)", "Critical intersections (articulation points) and bridge roads"],
])
p("The A* heuristic is the straight-line distance, divided by the network's maximum speed limit "
  "when optimising time. It never overestimates the true cost, so A* returns the same optimal "
  "answer as Dijkstra.")

# ------------------------------------------------------- 3 implementation
h("3. Implementation")
bullets([
    "Language and libraries: Python 3, matplotlib (maps and charts), Streamlit (dashboard), pytest (tests), python-docx (this report).",
    "Alternative routing: the busiest (most congested) road on the primary route is removed from a copy of the graph and Dijkstra is re-run.",
    "Incident handling: a road can be closed or its congestion changed at runtime; all routes are recomputed on the updated graph.",
    "Hotspot analysis: shortest paths are computed for many random origin-destination pairs and the number of trips through each intersection is counted.",
    "Critical infrastructure: Tarjan's low-link method finds intersections and roads whose failure would disconnect the network.",
])
h("Sample dataset", 2)
p(f"{log[0]}. The city is a 12 x 10 grid with faster, busier arterial roads, a few missing links "
  "and diagonal shortcuts, so it contains realistic bottlenecks. Data is stored in nodes.csv "
  "and edges.csv and can be replaced with any real network in the same format.")
h("Dashboard features", 2)
bullets([
    "Commuter routing: origin, destination, metric (time or distance), algorithm (Dijkstra or A*), route and alternative, nodes expanded, compute time.",
    "Network and incidents: edit congestion, close roads, simulate rush hour, live map with critical intersections.",
    "Infrastructure planning: MST backbone (Kruskal or Prim) and trip-load hotspot map.",
    "Performance: benchmark charts and complexity table.",
])
p("The dashboard (app.py) draws its maps with the same plotting module (smartcity/viz.py) "
  "that produced the figures in Section 4, so the route, MST, congestion and hotspot "
  "views in this report are exactly what the Commuter routing, Network, Infrastructure "
  "planning and Performance tabs display.")
h("3.1 Implementation evidence", 2)
SH = RES / "screenshots"
def shot(name, caption, w=5.9):
    d.add_picture(str(SH / name), width=Inches(w))
    d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = d.add_paragraph(caption)
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.runs[0].italic = True
p("Project structure: source package, data, tests, results and entry-point scripts.")
shot("shot1_structure.png", "Screenshot 1. Project folder structure.", 4.6)
p("Sample dataset: the first rows of the node and edge files and their sizes "
  "(120 intersections, 216 roads).")
shot("shot2_data.png", "Screenshot 2. Sample data files (nodes.csv and edges.csv).")

# ------------------------------------------------------------- 4 results
h("4. Results")
h("4.1 Network and congestion", 2)
fig("fig1_network.png", "Figure 1. Sample city coloured by congestion level.")
h("4.2 Route optimisation", 2)
p(log[1] + ".  " + (log[2] + "." if log[2].startswith("Alternative") else ""))
fig("fig2_route.png", "Figure 2. Fastest route (blue) and alternative avoiding the busiest road (purple).")
h("4.3 Incident re-routing", 2)
inc = [l for l in log if l.startswith("Incident")][0]
p(inc + ".")
fig("fig3_incident.png", "Figure 3. Route recomputed after a road on the original route is closed.")
h("4.4 Infrastructure planning with minimum spanning trees", 2)
mst = [l for l in log if l.startswith("MST")][0]
p(mst + ". Kruskal and Prim produce the same total weight, as expected.")
fig("fig4_mst.png", "Figure 4. Minimum spanning tree (blue) showing the cheapest connected road backbone.")
h("4.5 Critical infrastructure and hotspots", 2)
for l in log:
    if l.startswith(("Critical", "Roads with", "Top 5")):
        p(l + ".")
fig("fig5_hotspots.png", "Figure 5. Number of simulated trips passing through each intersection.")
shot("shot5_analysis.png", "Screenshot 3. Analysis output (results/run_log.txt) from running the full pipeline.")

# ---------------------------------------------------------- 5 performance
h("5. Performance Analysis")
p("Algorithms were timed on grid cities from 100 to 6,400 intersections. Query times are "
  "medians of 5 repeats, averaged over 20 random origin-destination pairs.")
table(["Nodes", "Edges", "BFS ms", "DFS ms", "Dijkstra ms", "A* ms", "Dijkstra expanded",
       "A* expanded", "Kruskal ms", "Prim ms"],
      [[r["nodes"], r["edges"], r["bfs_ms"], r["dfs_ms"], r["dijkstra_ms"], r["astar_ms"],
        r["dijkstra_expanded"], r["astar_expanded"], r["kruskal_ms"], r["prim_ms"]]
       for r in bench])
shot("shot4_benchmark.png", "Screenshot 4. Benchmark output (results/benchmark.csv).")
fig("fig6_benchmark.png", "Figure 6. Runtime growth and search effort of A* versus Dijkstra.", 6.2)
last = bench[-1]
ratio = float(last["dijkstra_expanded"]) / float(last["astar_expanded"])
p(f"All algorithms grow roughly linearly (with a log factor for the heap-based ones) in network "
  f"size. On the largest network A* expanded {last['astar_expanded']} nodes per query against "
  f"{last['dijkstra_expanded']} for Dijkstra, about {ratio:.1f} times fewer, because the "
  f"heuristic steers the search toward the destination. Kruskal and Prim perform similarly; "
  f"Prim's heap-based version is slightly slower here because the grid is sparse.")

# ------------------------------------------------------------- 6 testing
h("6. Testing")
p("Testing uses pytest (40 tests, all passing).")
table(["Test", "What it checks"], [
    ["BFS/DFS coverage, hop counts, components", "Traversals visit exactly the reachable nodes; isolated node forms its own component"],
    ["Dijkstra on hand-checked graph", "Path [0,1,2,5] with cost 3 km"],
    ["Unreachable destination", "Dijkstra and A* return None"],
    ["Congestion and closure", "Higher congestion raises travel time; closed road never appears in a route"],
    ["MST on small graph", "Kruskal and Prim both give weight 5 with 5 edges"],
    ["Bridges and articulation points", "Detected after deleting edges to create a weak link"],
    ["A* vs Dijkstra (20 random graphs x 10 queries)", "Identical optimal cost for both metrics"],
    ["Kruskal vs Prim (10 random graphs)", "Identical MST weight"],
])
shot("shot3_tests.png", "Screenshot 5. pytest run: all 40 tests passed.", 5.2)
p("During development the tests caught a defect in Prim's priority queue (ties in edge weight "
  "caused the heap to compare Edge objects); it was fixed by adding a tie-breaker counter.")

# ----------------------------------------------------------- 7 conclusion
h("7. Conclusion and Future Work")
p("The system shows that classic graph algorithms can power a practical traffic decision-support "
  "tool: Dijkstra and A* give commuters fast routes and re-routes after incidents, BFS/DFS and "
  "Tarjan analysis reveal connectivity and fragile points, and minimum spanning trees and "
  "hotspot counts guide infrastructure investment. Randomised cross-checks and benchmarks "
  "give confidence in both correctness and scalability.")
h("Limitations and future work", 2)
bullets([
    "Roads are undirected and congestion is static between user edits; real data would need one-way streets and time-of-day profiles.",
    "The sample city is synthetic; importing OpenStreetMap data would test the system on a real network.",
    "Possible extensions: live traffic feeds, turn penalties, multi-stop routing (travelling salesman heuristics), and Bellman-Ford for negative incentives such as toll rebates.",
])
h("Appendix: Execution log", 1)
for l in log:
    d.add_paragraph(l, style="List Bullet")

d.save(ROOT / "Capstone_Report.docx")
print("saved Capstone_Report.docx")
