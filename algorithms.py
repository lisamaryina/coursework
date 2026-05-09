"""
algorithms.py — алгоритми пошуку найкоротшого шляху.

Реалізовані алгоритми:
  - Dijkstra      : невід'ємні ваги, O((V+E) log V)
  - Bellman-Ford  : допускає від'ємні ваги, O(V·E)
  - A*            : евристичний, невід'ємні ваги
"""

from __future__ import annotations
import heapq
import math
from typing import Dict, List, Optional, Tuple

from graph import Graph


def _reconstruct_path(parent: Dict[str, Optional[str]],
                       start: str, end: str) -> List[str]:
    """Відновити шлях зі словника попередників."""
    path: List[str] = []
    current: Optional[str] = end
    while current is not None:
        path.append(current)
        current = parent.get(current)
    path.reverse()
    return path if path and path[0] == start else []


def dijkstra(graph: Graph, start: str,
             end: str) -> Tuple[List[str], float]:
    """
    Алгоритм Дейкстри.

    Умова: усі ваги ребер >= 0.
    Складність: O((V + E) log V).

    Повертає (path, distance). Якщо шлях відсутній — ([], inf).
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


def bellman_ford(graph: Graph, start: str,
                 end: str) -> Tuple[List[str], float]:
    """
    Алгоритм Беллмана-Форда.

    Підтримує від'ємні ваги. Виявляє від'ємні цикли.
    Складність: O(V · E).

    Повертає (path, distance). Якщо шлях відсутній — ([], inf).
    Підіймає ValueError при наявності від'ємного циклу.
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
                dist[v] = dist[u] + w
                parent[v] = u
                updated = True
            if not graph.directed and dist[v] != INF and dist[v] + w < dist[u]:
                dist[u] = dist[v] + w
                parent[u] = v
                updated = True
        if not updated:
            break

    # Перевірка на від'ємний цикл
    for u, v, w in edges:
        if dist[u] != INF and dist[u] + w < dist[v]:
            raise ValueError("Граф містить від'ємний цикл!")
        if not graph.directed and dist[v] != INF and dist[v] + w < dist[u]:
            raise ValueError("Граф містить від'ємний цикл!")

    if dist[end] == INF:
        return [], INF
    return _reconstruct_path(parent, start, end), dist[end]


def _euclidean(graph: Graph, u: str, goal: str) -> float:
    """
    Евристика A*.
    Для довільного зваженого графа використовується нульова евристика,
    щоб алгоритм завжди коректно знаходив найкоротший шлях.
    """
    return 0.0


def astar(graph: Graph, start: str,
          end: str) -> Tuple[List[str], float]:
    """
    Алгоритм A*.

    Умова: усі ваги ребер >= 0.
    Евристика: евклідова відстань (якщо координати задані),
               інакше еквівалентний алгоритму Дейкстри.

    Повертає (path, distance). Якщо шлях відсутній — ([], inf).
    """
    INF = float("inf")
    g_score: Dict[str, float] = {v: INF for v in graph.vertices}
    g_score[start] = 0.0
    f_score: Dict[str, float] = {v: INF for v in graph.vertices}
    f_score[start] = _euclidean(graph, start, end)
    parent: Dict[str, Optional[str]] = {v: None for v in graph.vertices}
    heap: List[Tuple[float, str]] = [(f_score[start], start)]
    closed: set = set()

    while heap:
        _, u = heapq.heappop(heap)
        if u in closed:
            continue
        if u == end:
            return _reconstruct_path(parent, start, end), g_score[end]
        closed.add(u)
        for v, w in graph.neighbors(u):
            if v in closed:
                continue
            tg = g_score[u] + w
            if tg < g_score[v]:
                g_score[v] = tg
                f_score[v] = tg + _euclidean(graph, v, end)
                parent[v] = u
                heapq.heappush(heap, (f_score[v], v))

    return [], INF
