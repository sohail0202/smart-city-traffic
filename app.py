"""Smart City Traffic Management dashboard.

Run:  streamlit run app.py
"""
import csv
import random
import time
from pathlib import Path

import streamlit as st

from smartcity import Graph, algorithms as A, viz

ROOT = Path(__file__).parent
st.set_page_config(page_title="Smart City Traffic", layout="wide")


@st.cache_data
def load_city():
    return Graph.from_csv(ROOT / "data/nodes.csv", ROOT / "data/edges.csv")


base = load_city()
if "city" not in st.session_state:
    st.session_state.city = base.copy()
g: Graph = st.session_state.city

names = {n: f"{d['name']} (#{n})" for n, d in g.nodes.items()}
by_label = {v: k for k, v in names.items()}
labels = list(names.values())

st.title("Smart City Traffic Management & Route Optimization")
tab_route, tab_net, tab_plan, tab_perf = st.tabs(
    ["Commuter routing", "Network & incidents", "Infrastructure planning", "Performance"])

# ------------------------------------------------------------------ routing
with tab_route:
    c1, c2, c3, c4 = st.columns([3, 3, 2, 2])
    src = by_label[c1.selectbox("From", labels, index=0)]
    dst = by_label[c2.selectbox("To", labels, index=len(labels) - 1)]
    metric = c3.radio("Optimise for", ["time", "distance"], horizontal=True)
    algo = c4.radio("Algorithm", ["Dijkstra", "A*"], horizontal=True)

    fn = A.dijkstra if algo == "Dijkstra" else A.astar
    stats: dict = {}
    t0 = time.perf_counter()
    res = fn(g, src, dst, metric, stats)
    ms = (time.perf_counter() - t0) * 1000
    if res is None:
        st.error("No route exists between these intersections (roads may be closed).")
    else:
        path, cost = res
        alt = A.alternative_route(g, src, dst, metric)
        unit = "min" if metric == "time" else "km"
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(f"Best route ({unit})", f"{cost:.1f}")
        m2.metric("Road segments", len(path) - 1)
        m3.metric("Nodes expanded", stats["expanded"])
        m4.metric("Compute time", f"{ms:.2f} ms")
        if alt:
            st.caption(f"Alternative avoiding the busiest road: {alt[1]:.1f} {unit} "
                       f"({alt[1] - cost:+.1f} {unit})")
        st.pyplot(viz.draw_network(g, "Recommended route", path=path,
                                   alt_path=alt[0] if alt else None))
        with st.expander("Turn-by-turn"):
            for i, n in enumerate(path, 1):
                st.write(f"{i}. {names[n]}")

# ------------------------------------------------------------------ network
with tab_net:
    left, right = st.columns([2, 1])
    with right:
        st.subheader("Simulate traffic")
        roads = [f"{e.u} – {e.v}  ({g.nodes[e.u]['name']} → {g.nodes[e.v]['name']})" for e in g.edges]
        pick = st.selectbox("Road", range(len(roads)), format_func=lambda i: roads[i])
        e = g.edges[pick]
        level = st.slider("Congestion", 0.0, 1.0, float(e.congestion), 0.05)
        b1, b2, b3 = st.columns(3)
        if b1.button("Apply"):
            g.set_congestion(e.u, e.v, level)
            st.rerun()
        if b2.button("Close road"):
            g.remove_edge(e.u, e.v)
            st.rerun()
        if b3.button("Reset city"):
            st.session_state.city = base.copy()
            st.rerun()
        if st.button("Random rush hour"):
            rnd = random.Random()
            for ed in rnd.sample(g.edges, k=len(g.edges) // 6):
                g.set_congestion(ed.u, ed.v, rnd.uniform(0.7, 1.0))
            st.rerun()
        st.subheader("Worst roads")
        for ed in A.congested_roads(g, 0.7)[:8]:
            st.write(f"{g.nodes[ed.u]['name']} ↔ {g.nodes[ed.v]['name']}: {ed.congestion:.2f}")
        comps = A.connected_components(g)
        st.write(f"Connected components: **{len(comps)}**")
    with left:
        aps = A.articulation_points(g)
        st.pyplot(viz.draw_network(g, "Live congestion map", highlight_nodes=aps))
        st.caption(f"Magenta rings: {len(aps)} critical intersection(s) whose closure "
                   f"would split the network. Bridge roads: {len(A.bridges(g))}.")

    with st.expander("Traversal explorer (BFS / DFS)"):
        start = by_label[st.selectbox("Start", labels, key="trav")]
        hops = A.bfs_hops(g, start)
        k = st.slider("Hops from start", 1, max(hops.values()), 5)
        reach = [n for n, h in hops.items() if h <= k]
        st.write(f"{len(reach)} intersections within {k} road segments. "
                 f"BFS order: {A.bfs(g, start)[:15]} …  DFS order: {A.dfs(g, start)[:15]} …")

# ----------------------------------------------------------------- planning
with tab_plan:
    pm = st.radio("Minimise", ["distance", "time"], horizontal=True, key="pm")
    which = st.radio("MST algorithm", ["Kruskal", "Prim"], horizontal=True)
    tree, total = (A.kruskal if which == "Kruskal" else A.prim)(g, pm)
    full = sum(e.weight(pm) for e in g.edges)
    c1, c2, c3 = st.columns(3)
    c1.metric("Backbone roads", len(tree))
    c2.metric(f"Backbone total ({'km' if pm == 'distance' else 'min'})", f"{total:.1f}")
    c3.metric("Share of full network", f"{100 * total / full:.0f}%")
    st.pyplot(viz.draw_network(g, "Minimum spanning tree: cheapest connected backbone",
                               mst=tree, show_congestion=False))
    st.markdown("**Hotspot analysis** – simulate commuter trips and count how many pass "
                "through each intersection.")
    n_trips = st.slider("Simulated trips", 50, 1000, 300, 50)
    rnd = random.Random(7)
    pairs = [tuple(rnd.sample(list(g.nodes), 2)) for _ in range(n_trips)]
    load = A.node_load(g, pairs)
    st.pyplot(viz.draw_heat(g, load))
    top = sorted(load, key=load.get, reverse=True)[:5]
    st.write("Candidate intersections for signal upgrades / extra lanes: " +
             ", ".join(f"**{g.nodes[n]['name']}** ({load[n]})" for n in top))

# -------------------------------------------------------------- performance
with tab_perf:
    bench = ROOT / "results/benchmark.csv"
    if bench.exists():
        with open(bench) as f:
            rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]
        st.pyplot(viz.draw_benchmark(rows))
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("Run `python benchmark.py` first to generate results/benchmark.csv.")
    st.markdown("""
| Algorithm | Complexity | Use in this system |
|---|---|---|
| BFS / DFS | O(V+E) | reachability, hop-distance, connected components |
| Dijkstra (heap) | O((V+E) log V) | fastest / shortest route |
| A* | O((V+E) log V) worst case, usually far fewer expansions | faster routing with straight-line heuristic |
| Kruskal | O(E log E) | cheapest road backbone |
| Prim (heap) | O(E log V) | cheapest road backbone (cross-check) |
| Tarjan low-link | O(V+E) | critical intersections and bridge roads |
""")
