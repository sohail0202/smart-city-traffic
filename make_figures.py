"""Generate the figures and log used in the capstone report.

Run:  python make_figures.py      (after python benchmark.py)
"""
import csv
import random
from pathlib import Path

from smartcity import Graph, algorithms as A, viz

ROOT = Path(__file__).parent
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

g = Graph.from_csv(ROOT / "data/nodes.csv", ROOT / "data/edges.csv")
log = []
def say(s):
    print(s)
    log.append(s)

say(f"Network: {len(g.nodes)} intersections, {len(g.edges)} roads, "
    f"{len(A.connected_components(g))} component(s)")

# 1. congestion map
viz.draw_network(g, "Sample city: road congestion").savefig(OUT / "fig1_network.png", dpi=130)

# 2. routing: fastest route + alternative
src, dst = 0, len(g.nodes) - 1
p_t, c_t = A.dijkstra(g, src, dst, "time")
p_d, c_d = A.dijkstra(g, src, dst, "distance")
alt = A.alternative_route(g, src, dst, "time")
say(f"Route {src}->{dst}: fastest {c_t:.1f} min over {len(p_t)-1} segments; "
    f"shortest {c_d:.2f} km over {len(p_d)-1} segments")
if alt:
    say(f"Alternative avoiding the busiest road: {alt[1]:.1f} min "
        f"(+{alt[1]-c_t:.1f} min)")
viz.draw_network(g, f"Fastest route {src} -> {dst} ({c_t:.1f} min)", path=p_t,
                 alt_path=alt[0] if alt else None).savefig(OUT / "fig2_route.png", dpi=130)

# 3. before/after an incident: close a road on the fastest route
g2 = g.copy()
u, v = p_t[len(p_t) // 2], p_t[len(p_t) // 2 + 1]
g2.remove_edge(u, v)
p2, c2 = A.dijkstra(g2, src, dst, "time")
say(f"Incident: road {u}-{v} closed -> new fastest route {c2:.1f} min "
    f"(+{c2 - c_t:.1f} min)")
viz.draw_network(g2, f"After closing road {u}-{v}: {c2:.1f} min", path=p2).savefig(
    OUT / "fig3_incident.png", dpi=130)

# 4. MST infrastructure backbone
kt, kw = A.kruskal(g, "distance")
pt, pw = A.prim(g, "distance", start=0)
say(f"MST (distance): Kruskal {kw:.2f} km, Prim {pw:.2f} km, "
    f"{len(kt)} roads kept of {len(g.edges)} "
    f"({100 * kw / sum(e.length_km for e in g.edges):.0f}% of total road length)")
viz.draw_network(g, f"Minimum spanning tree backbone ({kw:.1f} km)", mst=kt,
                 show_congestion=False).savefig(OUT / "fig4_mst.png", dpi=130)

# 5. critical infrastructure + congestion hotspots
aps, br = A.articulation_points(g), A.bridges(g)
say(f"Critical intersections (articulation points): {len(aps)}; bridge roads: {len(br)}")
hot = A.congested_roads(g, 0.7)
say(f"Roads with congestion >= 0.7: {len(hot)}")
rnd = random.Random(7)
pairs = [tuple(rnd.sample(list(g.nodes), 2)) for _ in range(300)]
load = A.node_load(g, pairs)
top = sorted(load, key=load.get, reverse=True)[:5]
say("Top 5 busiest intersections: " +
    ", ".join(f"{g.nodes[n]['name']} ({load[n]} trips)" for n in top))
viz.draw_heat(g, load).savefig(OUT / "fig5_hotspots.png", dpi=130)

# 6. benchmark chart
with open(OUT / "benchmark.csv") as f:
    rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]
viz.draw_benchmark(rows).savefig(OUT / "fig6_benchmark.png", dpi=130)

(OUT / "run_log.txt").write_text("\n".join(log) + "\n")
print("figures saved in", OUT)
