"""Matplotlib drawing helpers shared by the Streamlit dashboard and report figures."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402
from matplotlib import cm                            # noqa: E402
from matplotlib.collections import LineCollection    # noqa: E402

from .graph import Graph                             # noqa: E402


def _segments(g: Graph, edges):
    return [[(g.nodes[e.u]["x"], g.nodes[e.u]["y"]),
             (g.nodes[e.v]["x"], g.nodes[e.v]["y"])] for e in edges]


def draw_network(g: Graph, title: str = "", path: list[int] | None = None,
                 alt_path: list[int] | None = None, mst=None, highlight_nodes=None,
                 show_congestion: bool = True, ax=None, size=(9, 7)):
    """Draw roads coloured by congestion; optionally overlay a route / MST."""
    own = ax is None
    if own:
        fig, ax = plt.subplots(figsize=size)
    else:
        fig = ax.figure
    if show_congestion:
        lc = LineCollection(_segments(g, g.edges), array=[e.congestion for e in g.edges],
                            cmap="RdYlGn_r", linewidths=1.6, clim=(0, 1), alpha=0.85)
        ax.add_collection(lc)
        if own:
            fig.colorbar(lc, ax=ax, label="Congestion (0 free – 1 gridlock)", shrink=0.8)
    else:
        ax.add_collection(LineCollection(_segments(g, g.edges), colors="#bbb", linewidths=1))
    if mst:
        ax.add_collection(LineCollection(_segments(g, mst), colors="#1f4fd8", linewidths=3))

    def overlay(p, color, label, lw):
        xs = [g.nodes[n]["x"] for n in p]
        ys = [g.nodes[n]["y"] for n in p]
        ax.plot(xs, ys, color=color, linewidth=lw, label=label, zorder=5)
        ax.scatter([xs[0]], [ys[0]], c="green", s=90, zorder=6, edgecolor="k")
        ax.scatter([xs[-1]], [ys[-1]], c="red", s=90, zorder=6, edgecolor="k")

    if alt_path:
        overlay(alt_path, "#7b2cbf", "Alternative", 3)
    if path:
        overlay(path, "#0b3d91", "Fastest route", 4)
    if highlight_nodes:
        ax.scatter([g.nodes[n]["x"] for n in highlight_nodes],
                   [g.nodes[n]["y"] for n in highlight_nodes],
                   s=110, facecolors="none", edgecolors="magenta", linewidths=2, zorder=7,
                   label="Critical intersection")
    ax.autoscale()
    ax.set_aspect("equal")
    ax.set_xlabel("km")
    ax.set_ylabel("km")
    ax.set_title(title)
    if path or alt_path or highlight_nodes:
        ax.legend(loc="upper right", fontsize=8)
    return fig


def draw_heat(g: Graph, load: dict[int, int], title="Trip load per intersection", size=(9, 7)):
    fig, ax = plt.subplots(figsize=size)
    ax.add_collection(LineCollection(_segments(g, g.edges), colors="#ddd", linewidths=1))
    xs = [g.nodes[n]["x"] for n in g.nodes]
    ys = [g.nodes[n]["y"] for n in g.nodes]
    vals = [load[n] for n in g.nodes]
    sc = ax.scatter(xs, ys, c=vals, s=[20 + 8 * v for v in vals], cmap="plasma", zorder=3)
    fig.colorbar(sc, ax=ax, label="Number of trips passing through", shrink=0.8)
    ax.autoscale()
    ax.set_aspect("equal")
    ax.set_title(title)
    return fig


def draw_benchmark(rows, size=(10, 4)):
    n = [r["nodes"] for r in rows]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=size)
    for key, label in [("bfs_ms", "BFS"), ("dfs_ms", "DFS"), ("dijkstra_ms", "Dijkstra"),
                       ("astar_ms", "A*"), ("kruskal_ms", "Kruskal"), ("prim_ms", "Prim")]:
        a1.plot(n, [r[key] for r in rows], marker="o", label=label)
    a1.set_xlabel("Intersections")
    a1.set_ylabel("Time (ms)")
    a1.set_title("Runtime vs network size")
    a1.legend(fontsize=8)
    a1.grid(alpha=.3)
    a2.plot(n, [r["dijkstra_expanded"] for r in rows], marker="o", label="Dijkstra")
    a2.plot(n, [r["astar_expanded"] for r in rows], marker="o", label="A*")
    a2.set_xlabel("Intersections")
    a2.set_ylabel("Nodes expanded per query")
    a2.set_title("Search effort: A* vs Dijkstra")
    a2.legend()
    a2.grid(alpha=.3)
    fig.tight_layout()
    return fig
