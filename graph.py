"""
graph.py — клас Graph для представлення зваженого графу.
Підтримує орієнтовані та неорієнтовані зважені графи.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple


class Graph:
    """
    Зважений граф (орієнтований або неорієнтований).

    Атрибути:
        directed (bool): True — орієнтований граф.
        vertices (dict): {назва: позиція (x,y) або None}.
        adj (dict): список суміжності {u: [(v, weight), ...]}.
    """

    def __init__(self, directed: bool = False) -> None:
        self.directed: bool = directed
        self.vertices: Dict[str, Optional[Tuple[float, float]]] = {}
        self.adj: Dict[str, List[Tuple[str, float]]] = {}

    # ── Вершини ────────────────────────────────────────────
    def add_vertex(self, name: str,
                   pos: Optional[Tuple[float, float]] = None) -> None:
        """Додати вершину. Якщо вже існує — ігнорується."""
        if name in self.vertices:
            return
        self.vertices[name] = pos
        self.adj[name] = []

    def remove_vertex(self, name: str) -> None:
        """Видалити вершину та всі пов'язані ребра."""
        if name not in self.vertices:
            return
        del self.vertices[name]
        del self.adj[name]
        for u in self.adj:
            self.adj[u] = [(v, w) for v, w in self.adj[u] if v != name]

    # ── Ребра ───────────────────────────────────────────────
    def add_edge(self, u: str, v: str, weight: float) -> None:
        """Додати зважене ребро між u та v."""
        if u not in self.vertices:
            raise ValueError(f"Вершина '{u}' не існує.")
        if v not in self.vertices:
            raise ValueError(f"Вершина '{v}' не існує.")
        self.adj[u].append((v, weight))
        if not self.directed:
            self.adj[v].append((u, weight))

    def remove_last_edge(self) -> None:
        """Видалити останнє додане ребро (для графічного редактора)."""
        for u in reversed(list(self.adj)):
            if self.adj[u]:
                last_v, _ = self.adj[u][-1]
                self.adj[u].pop()
                if not self.directed:
                    self.adj[last_v] = [
                        (x, w) for x, w in self.adj[last_v] if x != u
                    ]
                return

    def get_edges(self) -> List[Tuple[str, str, float]]:
        """Повернути список усіх ребер (u, v, weight)."""
        edges, seen = [], set()
        for u in self.adj:
            for v, w in self.adj[u]:
                key = (u, v) if self.directed else tuple(sorted([u, v]))
                if key not in seen:
                    edges.append((u, v, w))
                    seen.add(key)
        return edges

    # ── Допоміжні ──────────────────────────────────────────
    def edge_count(self) -> int:
        return len(self.get_edges())

    def has_negative_weights(self) -> bool:
        return any(w < 0 for edges in self.adj.values() for _, w in edges)

    def neighbors(self, u: str) -> List[Tuple[str, float]]:
        return self.adj.get(u, [])

    def get_pos(self, v: str) -> Optional[Tuple[float, float]]:
        return self.vertices.get(v)

    def set_pos(self, v: str, pos: Tuple[float, float]) -> None:
        if v in self.vertices:
            self.vertices[v] = pos

    def clear(self) -> None:
        self.vertices.clear()
        self.adj.clear()

    def __repr__(self) -> str:
        kind = "орієнтований" if self.directed else "неорієнтований"
        return (f"Graph({kind}, вершин={len(self.vertices)}, "
                f"ребер={self.edge_count()})")
