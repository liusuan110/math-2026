"""图论与网络建模（networkx）：最短路 / 最小生成树 / 最大流 / TSP。

适用：B 题路径、连接、调度、网络结构类问题。
输入统一用「边列表」(u, v, weight)，便于赛时从表格数据快速建图。
"""
from __future__ import annotations

import networkx as nx


def build_graph(edges, directed=False) -> nx.Graph:
    """从边列表 [(u, v, w), ...] 建图。directed=True 建有向图。"""
    G = nx.DiGraph() if directed else nx.Graph()
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)
    return G


def shortest_path(G, source, target) -> dict:
    """最短路（Dijkstra，按 weight）。返回 {path, length}。"""
    path = nx.shortest_path(G, source, target, weight="weight")
    length = nx.shortest_path_length(G, source, target, weight="weight")
    return {"path": path, "length": length}


def mst(G) -> dict:
    """最小生成树（仅无向图）。返回 {edges, total_weight}。"""
    T = nx.minimum_spanning_tree(G, weight="weight")
    edges = [(u, v, d["weight"]) for u, v, d in T.edges(data=True)]
    return {"edges": edges, "total_weight": sum(w for *_, w in edges)}


def max_flow(G, source, sink) -> dict:
    """最大流（有向图，weight 视作容量）。返回 {flow_value, flow_dict}。"""
    val, flow = nx.maximum_flow(G, source, sink, capacity="weight")
    return {"flow_value": val, "flow_dict": flow}


def tsp(G) -> dict:
    """旅行商近似解（christofides/贪心）。返回 {route, length}。"""
    route = nx.approximation.traveling_salesman_problem(G, weight="weight", cycle=True)
    length = sum(G[route[i]][route[i + 1]]["weight"] for i in range(len(route) - 1))
    return {"route": route, "length": length}


if __name__ == "__main__":
    # 无向带权图
    edges = [("A", "B", 4), ("A", "C", 2), ("B", "C", 1),
             ("B", "D", 5), ("C", "D", 8), ("C", "E", 10), ("D", "E", 2)]
    G = build_graph(edges)
    sp = shortest_path(G, "A", "E")
    print(f"A->E 最短路: {sp['path']}, 长度 {sp['length']}")
    m = mst(G)
    print(f"最小生成树总权重: {m['total_weight']}, 边: {m['edges']}")
    t = tsp(G)
    print(f"TSP 近似回路: {t['route']}, 长度 {t['length']}")

    # 有向图最大流（weight=容量）
    dedges = [("s", "a", 10), ("s", "b", 5), ("a", "b", 15),
              ("a", "t", 10), ("b", "t", 10)]
    DG = build_graph(dedges, directed=True)
    f = max_flow(DG, "s", "t")
    print(f"s->t 最大流: {f['flow_value']}")
