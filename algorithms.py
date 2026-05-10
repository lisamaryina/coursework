"""
algorithms.py — алгоритми пошуку найкоротшого шляху.

  - Dijkstra      : невід'ємні ваги, O((V+E) log V)
  - Bellman-Ford  : допускає від'ємні ваги, O(V·E)
  - A*            : евристика за координатами або h=0;
                    від'ємні ваги — лише орієнтований граф (Джонсон)
"""

from __future__ import annotations
import heapq
import math
from typing import Dict, List, Optional, Tuple

from graph import Graph


def _reconstruct_path(parent: Dict[str, Optional[str]],
                      start: str, end: str) -> List[str]:
    path: List[str] = []
    cur: Optional[str] = end
    while cur is not None:
        path.append(cur)
        cur = parent.get(cur)
    path.reverse()
    return path if path and path[0] == start else []


def dijkstra(graph: Graph, start: str,
             end: str) -> Tuple[List[str], float]:
    """Алгоритм Дейкстри. Умова: всі ваги >= 0."""
    INF = float("inf")
    dist: Dict[str, float] = {v: INF for v in graph.vertices}
    dist[start] = 0.0
    parent: Dict[str, Optional[str]] = {v: None for v in graph.vertices}
    pq: List[Tuple[float, str]] = [(0.0, start)]
    while pq:
        d_u, u = heapq.heappop(pq)
        if d_u > dist[u]:
            continue
        if u == end:
            break
        for v, w in graph.neighbors(u):
            alt = dist[u] + w
            if alt < dist[v]:
                dist[v] = alt
                parent[v] = u
                heapq.heappush(pq, (alt, v))
    if dist[end] == INF:
        return [], INF
    return _reconstruct_path(parent, start, end), dist[end]


def bellman_ford(graph: Graph, start: str,
                 end: str) -> Tuple[List[str], float]:
    """Алгоритм Беллмана-Форда. Підтримує від'ємні ваги."""
    INF = float("inf")
    dist: Dict[str, float] = {v: INF for v in graph.vertices}
    dist[start] = 0.0
    parent: Dict[str, Optional[str]] = {v: None for v in graph.vertices}
    edges = graph.get_edges()
    for _ in range(len(graph.vertices) - 1):
        updated = False
        for u, v, w in edges:
            if dist[u] != INF and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w; parent[v] = u; updated = True
            if not graph.directed and dist[v] != INF and dist[v] + w < dist[u]:
                dist[u] = dist[v] + w; parent[u] = v; updated = True
        if not updated:
            break
    for u, v, w in edges:
        if dist[u] != INF and dist[u] + w < dist[v]:
            raise ValueError("Граф містить від'ємний цикл!")
        if not graph.directed and dist[v] != INF and dist[v] + w < dist[u]:
            raise ValueError("Граф містить від'ємний цикл!")
    if dist[end] == INF:
        return [], INF
    return _reconstruct_path(parent, start, end), dist[end]


def _johnson_potentials(graph: Graph) -> Optional[Dict[str, float]]:
    dist: Dict[str, float] = {v: 0.0 for v in graph.vertices}
    directed_edges = [(u, v, w) for u in graph.adj for v, w in graph.adj[u]]
    n = len(graph.vertices)
    for _ in range(n - 1):
        updated = False
        for u, v, w in directed_edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w; updated = True
        if not updated:
            break
    for u, v, w in directed_edges:
        if dist[u] + w < dist[v] - 1e-9:
            return None
    return dist


def astar(graph: Graph, start: str, end: str,
          coords: Optional[Dict[str, Tuple[float, float]]] = None
          ) -> Tuple[List[str], float]:
    """A* з перезважуванням Джонсона. Підтримує від'ємні ваги."""
    INF = float("inf")
    if not graph.directed and graph.has_negative_weights():
        raise ValueError(
            "A* не підтримує від'ємні ваги у неорієнтованому графі.\n"
            "Використайте алгоритм Беллмана-Форда.")
    h_pot = _johnson_potentials(graph)
    if h_pot is None:
        raise ValueError("Граф містить від'ємний цикл!\nA* не може знайти коректний шлях.")

    def heuristic(v: str) -> float:
        if not coords:
            return 0.0
        pv = coords.get(v); pe = coords.get(end)
        if pv and pe:
            return math.hypot(pv[0] - pe[0], pv[1] - pe[1])
        return 0.0

    g_score: Dict[str, float] = {v: INF for v in graph.vertices}
    g_score[start] = 0.0
    parent: Dict[str, Optional[str]] = {v: None for v in graph.vertices}
    heap: List[Tuple[float, str]] = [(heuristic(start), start)]
    closed: set = set()
    while heap:
        _, u = heapq.heappop(heap)
        if u in closed:
            continue
        if u == end:
            real_dist = g_score[end] + h_pot[end] - h_pot[start]
            return _reconstruct_path(parent, start, end), real_dist
        closed.add(u)
        for v, w in graph.neighbors(u):
            if v in closed:
                continue
            w_prime = w + h_pot[u] - h_pot[v]
            tg = g_score[u] + w_prime
            if tg < g_score[v]:
                g_score[v] = tg
                parent[v] = u
                heapq.heappush(heap, (tg + heuristic(v), v))
    return [], INF