"""Graph algorithms: traversal, shortest path, MST, and network analysis."""
from __future__ import annotations

import heapq
from collections import deque

from .graph import Graph

Path = tuple[list[int], float]   # (node sequence, total cost)


# ---------------------------------------------------------------- traversal
def bfs(g: Graph, start: int) -> list[int]:
    """Breadth-first order: reachable intersections by fewest road segments."""
    seen, order, q = {start}, [], deque([start])
    while q:
        u = q.popleft()
        order.append(u)
        for v, _ in sorted(g.neighbors(u), key=lambda t: t[0]):
            if v not in seen:
                seen.add(v)
                q.append(v)
    return order


def dfs(g: Graph, start: int) -> list[int]:
    """Iterative depth-first order."""
    seen, order, stack = set(), [], [start]
    while stack:
        u = stack.pop()
        if u in seen:
            continue
        seen.add(u)
        order.append(u)
        for v, _ in sorted(g.neighbors(u), key=lambda t: -t[0]):
            if v not in seen:
                stack.append(v)
    return order


def bfs_hops(g: Graph, start: int) -> dict[int, int]:
    """Number of road segments from start to every reachable node."""
    dist, q = {start: 0}, deque([start])
    while q:
        u = q.popleft()
        for v, _ in g.neighbors(u):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def connected_components(g: Graph) -> list[list[int]]:
    seen, comps = set(), []
    for n in g.nodes:
        if n not in seen:
            comp = dfs(g, n)
            seen.update(comp)
            comps.append(sorted(comp))
    return comps


# ------------------------------------------------------------ shortest path
def _rebuild(prev: dict[int, int], src: int, dst: int) -> list[int]:
    path, cur = [dst], dst
    while cur != src:
        cur = prev[cur]
        path.append(cur)
    return path[::-1]


def dijkstra(g: Graph, src: int, dst: int, metric: str = "time",
             stats: dict | None = None) -> Path | None:
    """Shortest path with a binary heap. Returns None if unreachable."""
    dist, prev, heap = {src: 0.0}, {}, [(0.0, src)]
    visited = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        if u == dst:
            if stats is not None:
                stats["expanded"] = len(visited)
            return _rebuild(prev, src, dst), d
        for v, e in g.neighbors(u):
            nd = d + e.weight(metric)
            if nd < dist.get(v, float("inf")):
                dist[v], prev[v] = nd, u
                heapq.heappush(heap, (nd, v))
    if stats is not None:
        stats["expanded"] = len(visited)
    return None


def astar(g: Graph, src: int, dst: int, metric: str = "time",
          stats: dict | None = None) -> Path | None:
    """A* with an admissible straight-line heuristic.

    For 'time' the heuristic divides distance by the fastest speed limit in the
    network, so it never overestimates the true travel time.
    """
    vmax = max((e.speed_kmh for e in g.edges), default=1.0)

    def h(n: int) -> float:
        d = g.euclid_km(n, dst)
        return d if metric == "distance" else d / vmax * 60.0

    gscore, prev = {src: 0.0}, {}
    heap, closed = [(h(src), 0.0, src)], set()
    while heap:
        _, gs, u = heapq.heappop(heap)
        if u in closed:
            continue
        closed.add(u)
        if u == dst:
            if stats is not None:
                stats["expanded"] = len(closed)
            return _rebuild(prev, src, dst), gs
        for v, e in g.neighbors(u):
            ng = gs + e.weight(metric)
            if ng < gscore.get(v, float("inf")):
                gscore[v], prev[v] = ng, u
                heapq.heappush(heap, (ng + h(v), ng, v))
    if stats is not None:
        stats["expanded"] = len(closed)
    return None


def dijkstra_all(g: Graph, src: int, metric: str = "time") -> dict[int, float]:
    """Single-source shortest costs to every node (used for accessibility)."""
    dist, heap = {src: 0.0}, [(0.0, src)]
    done = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in done:
            continue
        done.add(u)
        for v, e in g.neighbors(u):
            nd = d + e.weight(metric)
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist


def alternative_route(g: Graph, src: int, dst: int, metric: str = "time") -> Path | None:
    """Best route that avoids the busiest road of the primary route."""
    best = dijkstra(g, src, dst, metric)
    if not best or len(best[0]) < 2:
        return None
    path = best[0]
    worst = max(zip(path, path[1:]),
                key=lambda p: next(e.congestion for _, e in g.neighbors(p[0]) if e.v == p[1]))
    g2 = g.copy()
    g2.remove_edge(*worst)
    return dijkstra(g2, src, dst, metric)


# ------------------------------------------------------- spanning tree (MST)
class DisjointSet:
    def __init__(self, items):
        self.parent = {i: i for i in items}
        self.rank = {i: 0 for i in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def kruskal(g: Graph, metric: str = "distance"):
    """Minimum spanning forest. Returns (edges, total_weight)."""
    ds = DisjointSet(g.nodes)
    tree, total = [], 0.0
    for e in sorted(g.edges, key=lambda e: e.weight(metric)):
        if ds.union(e.u, e.v):
            tree.append(e)
            total += e.weight(metric)
    return tree, total


def prim(g: Graph, metric: str = "distance", start: int | None = None):
    """Prim's MST (heap based) for the component containing `start`."""
    if not g.nodes:
        return [], 0.0
    start = next(iter(g.nodes)) if start is None else start
    seen, tree, total = {start}, [], 0.0
    tick = 0                                   # tie-breaker so Edge is never compared
    heap = []
    for e in g.adj[start]:
        heap.append((e.weight(metric), tick, e))
        tick += 1
    heapq.heapify(heap)
    while heap:
        w, _, e = heapq.heappop(heap)
        v = e.v
        if v in seen:
            continue
        seen.add(v)
        tree.append(e)
        total += w
        for e2 in g.adj[v]:
            if e2.v not in seen:
                heapq.heappush(heap, (e2.weight(metric), tick, e2))
                tick += 1
    return tree, total


# ----------------------------------------------------------- network analysis
def articulation_points(g: Graph) -> set[int]:
    """Intersections whose closure disconnects the network (critical nodes)."""
    disc, low, aps, timer = {}, {}, set(), [0]

    def visit(u, parent):
        disc[u] = low[u] = timer[0]
        timer[0] += 1
        children = 0
        for v, _ in g.neighbors(u):
            if v == parent:
                continue
            if v in disc:
                low[u] = min(low[u], disc[v])
            else:
                children += 1
                visit(v, u)
                low[u] = min(low[u], low[v])
                if parent is not None and low[v] >= disc[u]:
                    aps.add(u)
        if parent is None and children > 1:
            aps.add(u)

    for n in g.nodes:
        if n not in disc:
            visit(n, None)
    return aps


def bridges(g: Graph) -> list[tuple[int, int]]:
    """Roads whose closure disconnects the network."""
    disc, low, out, timer = {}, {}, [], [0]

    def visit(u, parent):
        disc[u] = low[u] = timer[0]
        timer[0] += 1
        for v, _ in g.neighbors(u):
            if v == parent:
                continue
            if v in disc:
                low[u] = min(low[u], disc[v])
            else:
                visit(v, u)
                low[u] = min(low[u], low[v])
                if low[v] > disc[u]:
                    out.append((u, v))

    for n in g.nodes:
        if n not in disc:
            visit(n, None)
    return out


def congested_roads(g: Graph, threshold: float = 0.7):
    return sorted((e for e in g.edges if e.congestion >= threshold),
                  key=lambda e: -e.congestion)


def node_load(g: Graph, pairs: list[tuple[int, int]], metric: str = "time") -> dict[int, int]:
    """How many sample trips pass through each intersection (hotspot finder)."""
    load = {n: 0 for n in g.nodes}
    for s, t in pairs:
        r = dijkstra(g, s, t, metric)
        if r:
            for n in r[0]:
                load[n] += 1
    return load
