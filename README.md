# Smart City Traffic Management and Route Optimization System

Models a city road network as a weighted graph and uses graph algorithms for routing,
traffic analysis and infrastructure planning, with an interactive dashboard.

| Need | Algorithm | File |
|---|---|---|
| Reachability, hop distance, components | BFS, DFS | `smartcity/algorithms.py` |
| Fastest / shortest route | Dijkstra, A* | `smartcity/algorithms.py` |
| Alternative route when the busiest road is avoided | Dijkstra on a modified copy | `alternative_route` |
| Cheapest road backbone | Kruskal (union-find), Prim (heap) | `kruskal`, `prim` |
| Critical intersections / bridge roads | Tarjan low-link | `articulation_points`, `bridges` |
| Hotspots | repeated shortest paths over simulated trips | `node_load` |

**Edge weight.** Distance (km) or travel time (min). Travel time = free-flow time x
(1 + 2 x congestion^2), so a jammed road (congestion 1.0) takes 3x longer.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python data/generate_sample.py   # (optional) regenerate sample city: 120 nodes, 216 roads
python -m pytest -q              # 40 unit / cross-check tests
python benchmark.py              # writes results/benchmark.csv
python make_figures.py           # writes results/*.png and results/run_log.txt
streamlit run app.py             # interactive dashboard
python make_report.py            # builds Capstone_Report.docx from the results
```

## Dashboard

1. **Commuter routing** – pick origin/destination, optimise for time or distance, choose Dijkstra or A*; see route, alternative, nodes expanded, compute time.
2. **Network & incidents** – set congestion, close roads, random rush hour; live map with critical intersections.
3. **Infrastructure planning** – MST backbone (Kruskal/Prim) and trip-load hotspot map.
4. **Performance** – runtime and search-effort charts plus complexity table.

## Project layout

```
smartcity/       graph.py, algorithms.py, viz.py
data/            nodes.csv, edges.csv, generate_sample.py
tests/           test_algorithms.py
results/         benchmark.csv, figures, run_log.txt
app.py  benchmark.py  make_figures.py  make_report.py
```

## Using your own city

Provide `nodes.csv` (`id,name,x,y`, coordinates in km) and `edges.csv`
(`u,v,length_km,speed_kmh,congestion`) and point `Graph.from_csv` at them.

## Testing

`tests/test_algorithms.py` covers hand-checked small graphs (paths, unreachable nodes,
closures, MST weight, bridges) and randomised cross-checks: A* = Dijkstra on 20 random
graphs, Kruskal = Prim on 10.
