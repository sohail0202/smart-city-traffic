"""Benchmark the algorithms on growing grid cities and write results/benchmark.csv + log.

Run:  python benchmark.py
"""
import csv
import random
import statistics
import time
from pathlib import Path

from smartcity import Graph, algorithms as A

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)


def grid_city(side: int, seed: int = 1) -> Graph:
    rnd = random.Random(seed)
    g = Graph()
    for r in range(side):
        for c in range(side):
            g.add_node(r * side + c, f"{c}-{r}", c * 0.5, r * 0.5)
    for r in range(side):
        for c in range(side):
            n = r * side + c
            if c + 1 < side:
                g.add_edge(n, n + 1, 0.5, rnd.choice([40, 60]), rnd.random() * 0.8)
            if r + 1 < side:
                g.add_edge(n, n + side, 0.5, rnd.choice([40, 60]), rnd.random() * 0.8)
    return g


def timeit(fn, repeats=5):
    ts = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        ts.append((time.perf_counter() - t0) * 1000)
    return statistics.median(ts)


rows = []
for side in (10, 20, 40, 60, 80):
    g = grid_city(side)
    n, m = len(g.nodes), len(g.edges)
    rnd = random.Random(side)
    pairs = [tuple(rnd.sample(range(n), 2)) for _ in range(20)]
    st_d, st_a = [], []
    for s, t in pairs:
        sd, sa = {}, {}
        A.dijkstra(g, s, t, "time", sd)
        A.astar(g, s, t, "time", sa)
        st_d.append(sd["expanded"])
        st_a.append(sa["expanded"])
    rows.append({
        "nodes": n, "edges": m,
        "bfs_ms": round(timeit(lambda: A.bfs(g, 0)), 3),
        "dfs_ms": round(timeit(lambda: A.dfs(g, 0)), 3),
        "dijkstra_ms": round(timeit(lambda: [A.dijkstra(g, s, t) for s, t in pairs]) / 20, 3),
        "astar_ms": round(timeit(lambda: [A.astar(g, s, t) for s, t in pairs]) / 20, 3),
        "dijkstra_expanded": round(statistics.mean(st_d), 1),
        "astar_expanded": round(statistics.mean(st_a), 1),
        "kruskal_ms": round(timeit(lambda: A.kruskal(g)), 3),
        "prim_ms": round(timeit(lambda: A.prim(g)), 3),
    })
    print(rows[-1])

with open(OUT / "benchmark.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
print(f"saved {OUT / 'benchmark.csv'}")
