"""
algorithms.py — алгоритми пошуку найкоротшого шляху.

  - Dijkstra      : невід'ємні ваги, O((V+E) log V)
  - Bellman-Ford  : допускає від'ємні ваги, O(V·E)
  - A*            : евристика за координатами (евклідова) або h=0;
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


# ──────────────────────────────────────────────────────
#  1. Дейкстра
# ──────────────────────────────────────────────────────
def dijkstra(graph: Graph, start: str,
             end: str) -> Tuple[List[str], float]:
    """
    Алгоритм Дейкстри.
    Умова: всі ваги >= 0. Складність O((V+E) log V).
    """
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


# ──────────────────────────────────────────────────────
#  2. Беллман-Форд
# ──────────────────────────────────────────────────────
def bellman_ford(graph: Graph, start: str,
                 end: str) -> Tuple[List[str], float]:
    """
    Алгоритм Беллмана-Форда.
    Підтримує від'ємні ваги. Виявляє від'ємні цикли.
    Складність O(V·E).
    """
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


# ──────────────────────────────────────────────────────
#  3. A* з перезважуванням Джонсона
# ──────────────────────────────────────────────────────
def _johnson_potentials(graph: Graph) -> Optional[Dict[str, float]]:
    """
    Потенціали Джонсона через Беллмана-Форда з фіктивним джерелом.
    Всі початкові відстані = 0 (фіктивне джерело з'єднане з усіма).
    Працює лише на орієнтованих ребрах.
    """
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
    """
    Алгоритм A* з перезважуванням Джонсона.

    Підтримує від'ємні ваги ТІЛЬКИ для орієнтованого графу
    (неорієнтований граф з від'ємною вагою = від'ємний цикл A->B->A).

    Евристика:
      - якщо coords задано: евклідова відстань між вершинами
      - інакше: h(v) = 0 (алгоритм поводиться як Дейкстра)

    coords — словник {назва_вершини: (x, y)}, необов'язковий.

    Перезважування Джонсона:
        w'(u,v) = w(u,v) + h_pot[u] - h_pot[v] >= 0
    Реальна відстань: g[end] + h_pot[end] - h_pot[start]
    """
    INF = float("inf")

    if not graph.directed and graph.has_negative_weights():
        raise ValueError(
            "A* не підтримує від'ємні ваги у неорієнтованому графі.\n"
            "Ребро A–B з від'ємною вагою утворює цикл A→B→A.\n"
            "Використайте алгоритм Беллмана-Форда.")

    # Потенціали Джонсона (для підтримки від'ємних ваг)
    h_pot = _johnson_potentials(graph)
    if h_pot is None:
        raise ValueError(
            "Граф містить від'ємний цикл!\n"
            "A* не може знайти коректний шлях.")

    # Евристична функція (евклідова якщо є координати, інакше 0)
    def heuristic(v: str) -> float:
        if not coords:
            return 0.0
        pv = coords.get(v)
        pe = coords.get(end)
        if pv and pe:
            return math.hypot(pv[0] - pe[0], pv[1] - pe[1])
        return 0.0

    # A* на перезважених ребрах
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
            w_prime = w + h_pot[u] - h_pot[v]  # >= 0
            tg = g_score[u] + w_prime
            if tg < g_score[v]:
                g_score[v] = tg
                parent[v] = u
                f = tg + heuristic(v)
                heapq.heappush(heap, (f, v))

    return [], INF