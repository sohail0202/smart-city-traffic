import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from smartcity import Graph, algorithms as A   # noqa: E402


@pytest.fixture
def small():
    """
        0 --1-- 1 --1-- 2
        |       |       |
        4       1       1
        |       |       |
        3 --1-- 4 --5-- 5     (node 6 isolated)
    """
    g = Graph()
    for i, (x, y) in enumerate([(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (9, 9)]):
        g.add_node(i, f"n{i}", x, y)
    for u, v, km in [(0, 1, 1), (1, 2, 1), (0, 3, 4), (1, 4, 1), (2, 5, 1), (3, 4, 1), (4, 5, 5)]:
        g.add_edge(u, v, km, 60, 0.0)
    return g


def test_bfs_dfs_cover_component(small):
    assert sorted(A.bfs(small, 0)) == [0, 1, 2, 3, 4, 5]
    assert sorted(A.dfs(small, 0)) == [0, 1, 2, 3, 4, 5]
    assert A.bfs(small, 0)[0] == 0


def test_bfs_hops(small):
    h = A.bfs_hops(small, 0)
    assert h[5] == 3 and h[4] == 2 and 6 not in h


def test_components(small):
    comps = A.connected_components(small)
    assert len(comps) == 2 and [6] in comps


def test_dijkstra_distance(small):
    path, d = A.dijkstra(small, 0, 5, "distance")
    assert d == 3 and path == [0, 1, 2, 5]


def test_unreachable(small):
    assert A.dijkstra(small, 0, 6) is None
    assert A.astar(small, 0, 6) is None


def test_congestion_changes_route(small):
    base_path, base_cost = A.dijkstra(small, 0, 5, "time")
    small.set_congestion(0, 1, 1.0)
    new_path, new_cost = A.dijkstra(small, 0, 5, "time")
    assert new_cost > base_cost                  # congestion raises travel time
    # a long detour (0-3-4-5 = 10 km) only wins once the main road is jammed enough
    for e in small.edges:
        if {e.u, e.v} == {1, 2}:
            small.set_congestion(1, 2, 1.0)
    small.set_congestion(2, 5, 1.0)
    detour_path, _ = A.dijkstra(small, 0, 5, "time")
    assert detour_path[0] == 0 and detour_path[-1] == 5


def test_road_closure(small):
    small.remove_edge(1, 2)
    path, _ = A.dijkstra(small, 0, 5, "distance")
    assert (1, 2) not in list(zip(path, path[1:]))


def test_mst_weight_and_edges(small):
    kt, kw = A.kruskal(small, "distance")
    pt, pw = A.prim(small, "distance", start=0)
    assert len(kt) == 5 and len(pt) == 5          # 6 connected nodes -> 5 edges
    assert kw == pw == 5                           # 1+1+1+1+1


def test_articulation_and_bridges(small):
    assert A.articulation_points(small) == set()
    g = small.copy()
    g.remove_edge(1, 4)
    g.remove_edge(3, 4)                            # node 4 now hangs on 4-5
    assert 5 in A.articulation_points(g)
    assert (4, 5) in A.bridges(g) or (5, 4) in A.bridges(g)


def random_graph(n, m, seed):
    rnd = random.Random(seed)
    g = Graph()
    for i in range(n):
        g.add_node(i, str(i), rnd.random() * 10, rnd.random() * 10)
    for i in range(1, n):                          # spanning backbone
        j = rnd.randrange(i)
        g.add_edge(i, j, g.euclid_km(i, j) + 0.1, rnd.choice([30, 50, 70]), rnd.random())
    for _ in range(m):
        a, b = rnd.sample(range(n), 2)
        g.add_edge(a, b, g.euclid_km(a, b) + 0.1, rnd.choice([30, 50, 70]), rnd.random())
    return g


@pytest.mark.parametrize("seed", range(10))
@pytest.mark.parametrize("metric", ["distance", "time"])
def test_astar_matches_dijkstra(seed, metric):
    g = random_graph(60, 90, seed)
    rnd = random.Random(seed)
    for _ in range(10):
        s, t = rnd.sample(range(60), 2)
        d1 = A.dijkstra(g, s, t, metric)[1]
        d2 = A.astar(g, s, t, metric)[1]
        assert d1 == pytest.approx(d2)


@pytest.mark.parametrize("seed", range(10))
def test_kruskal_equals_prim(seed):
    g = random_graph(50, 80, seed)
    assert A.kruskal(g)[1] == pytest.approx(A.prim(g)[1])


def test_dijkstra_all_agrees(small):
    d = A.dijkstra_all(small, 0, "distance")
    assert d[5] == A.dijkstra(small, 0, 5, "distance")[1]
