"""Road network model: intersections are nodes, roads are weighted edges."""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Edge:
    u: int
    v: int
    length_km: float
    speed_kmh: float      # free-flow speed limit
    congestion: float     # 0.0 (empty) .. 1.0 (gridlock)

    def travel_time_min(self) -> float:
        """Travel time in minutes, slowed by congestion (BPR-style penalty)."""
        free_flow = self.length_km / self.speed_kmh * 60.0
        return free_flow * (1.0 + 2.0 * self.congestion ** 2)

    def weight(self, metric: str) -> float:
        if metric == "distance":
            return self.length_km
        if metric == "time":
            return self.travel_time_min()
        raise ValueError(f"unknown metric: {metric}")


class Graph:
    """Undirected road network stored as an adjacency list."""

    def __init__(self) -> None:
        self.nodes: dict[int, dict] = {}          # id -> {name, x, y}
        self.adj: dict[int, list[Edge]] = {}
        self.edges: list[Edge] = []

    def add_node(self, node_id: int, name: str, x: float, y: float) -> None:
        self.nodes[node_id] = {"name": name, "x": x, "y": y}
        self.adj.setdefault(node_id, [])

    def add_edge(self, u: int, v: int, length_km: float, speed_kmh: float,
                 congestion: float = 0.0) -> None:
        if u not in self.nodes or v not in self.nodes:
            raise KeyError("both endpoints must exist before adding an edge")
        e = Edge(u, v, length_km, speed_kmh, congestion)
        self.edges.append(e)
        self.adj[u].append(e)
        self.adj[v].append(Edge(v, u, length_km, speed_kmh, congestion))

    def neighbors(self, u: int):
        for e in self.adj[u]:
            yield e.v, e

    def euclid_km(self, a: int, b: int) -> float:
        """Straight-line distance (map units are km) used by A*."""
        na, nb = self.nodes[a], self.nodes[b]
        return math.hypot(na["x"] - nb["x"], na["y"] - nb["y"])

    def set_congestion(self, u: int, v: int, value: float) -> None:
        """Update congestion on road u-v (both directions)."""
        value = min(max(value, 0.0), 1.0)
        found = False
        for src, dst in ((u, v), (v, u)):
            for i, e in enumerate(self.adj[src]):
                if e.v == dst:
                    self.adj[src][i] = Edge(src, dst, e.length_km, e.speed_kmh, value)
                    found = True
        if not found:
            raise KeyError(f"no road between {u} and {v}")
        for i, e in enumerate(self.edges):
            if {e.u, e.v} == {u, v}:
                self.edges[i] = Edge(e.u, e.v, e.length_km, e.speed_kmh, value)

    def remove_edge(self, u: int, v: int) -> None:
        """Close a road (accident / construction)."""
        self.adj[u] = [e for e in self.adj[u] if e.v != v]
        self.adj[v] = [e for e in self.adj[v] if e.v != u]
        self.edges = [e for e in self.edges if {e.u, e.v} != {u, v}]

    def copy(self) -> "Graph":
        g = Graph()
        for nid, d in self.nodes.items():
            g.add_node(nid, d["name"], d["x"], d["y"])
        for e in self.edges:
            g.add_edge(e.u, e.v, e.length_km, e.speed_kmh, e.congestion)
        return g

    @classmethod
    def from_csv(cls, nodes_path: str | Path, edges_path: str | Path) -> "Graph":
        g = cls()
        with open(nodes_path, newline="") as f:
            for r in csv.DictReader(f):
                g.add_node(int(r["id"]), r["name"], float(r["x"]), float(r["y"]))
        with open(edges_path, newline="") as f:
            for r in csv.DictReader(f):
                g.add_edge(int(r["u"]), int(r["v"]), float(r["length_km"]),
                           float(r["speed_kmh"]), float(r["congestion"]))
        return g
