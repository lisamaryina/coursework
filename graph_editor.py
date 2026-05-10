"""
graph_editor.py — інтерактивний графічний редактор графу.

Можливості:
  • Клік на вільному місці = нова вершина (автоназва A, B, ...)
  • Клік по двох вершинах = ребро (вводиться вага)
  • Відмінити останнє ребро / Очистити весь граф
  • Кнопка «Готово» передає граф у головне вікно
"""

from __future__ import annotations
import math
from typing import Callable, Optional
import tkinter as tk
from tkinter import simpledialog, messagebox

from graph import Graph

VERTEX_RADIUS = 20
CANVAS_W = 720
CANVAS_H = 500
VERTEX_COLORS = [
    "#1a6aff", "#1a8a1a", "#cc5500", "#7700cc",
    "#cc0000", "#007777", "#886600", "#333399",
]


class GraphEditorWindow(tk.Toplevel):
    """
    Вікно графічного введення графу.
    Успадковує tk.Toplevel, дотримується принципу єдиної відповідальності:
    відповідає лише за введення графу мишею.
    """

    def __init__(self, master: tk.Tk, directed: bool,
                 on_done: Callable[[Graph], None]) -> None:
        super().__init__(master)
        self.title("Графічне введення графу")
        self.resizable(True, True)

        self._directed: bool = directed
        self._on_done: Callable[[Graph], None] = on_done
        self._graph: Graph = Graph(directed=directed)
        self._selected: Optional[str] = None

        self._build_ui()
        self.lift()
        self.focus_force()

    # ── Побудова UI ────────────────────────────────────────
    def _build_ui(self) -> None:
        self._build_toolbar()
        self._build_canvas()
        self._build_statusbar()
        self._redraw()

    def _build_toolbar(self) -> None:
        tb = tk.Frame(self, pady=6, padx=10)
        tb.pack(fill="x")
        tk.Label(
            tb,
            text="Клік на вільному місці = вершина  |  Клік 2 вершин = ребро",
            font=("Helvetica", 9),
        ).pack(side="left")
        for text, cmd in [
            ("Готово", self._done),
            ("Очистити", self._clear),
            ("Відмінити останнє ребро", self._undo),
        ]:
            tk.Button(tb, text=text, command=cmd,
                       font=("Helvetica", 9), padx=6).pack(side="right", padx=3)

    def _build_canvas(self) -> None:
        self._canvas = tk.Canvas(
            self,
            width=CANVAS_W,
            height=CANVAS_H,
            bg="white",
            highlightthickness=1,
            highlightbackground="#aaaaaa",
        )
        self._canvas.pack(fill="both", expand=True, padx=10, pady=4)
        self._canvas.bind("<Button-1>", self._on_click)

    def _build_statusbar(self) -> None:
        self._status_var = tk.StringVar(
            value="Клацніть на полотні щоб додати вершину")
        tk.Label(
            self,
            textvariable=self._status_var,
            font=("Helvetica", 9, "italic"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(0, 6))

    # ── Логіка редагування ─────────────────────────────────
    def _next_vertex_name(self) -> str:
        existing = set(self._graph.vertices)
        for i in range(26):
            name = chr(65 + i)
            if name not in existing:
                return name
        for suffix in range(1, 999):
            for i in range(26):
                name = chr(65 + i) + str(suffix)
                if name not in existing:
                    return name
        return str(len(existing))

    def _vertex_at(self, x: float, y: float) -> Optional[str]:
        for name, pos in self._graph.vertices.items():
            if pos and (x - pos[0])**2 + (y - pos[1])**2 <= VERTEX_RADIUS**2:
                return name
        return None

    def _on_click(self, event: tk.Event) -> None:
        x, y = float(event.x), float(event.y)
        hit = self._vertex_at(x, y)

        if hit is None:
            name = self._next_vertex_name()
            self._graph.add_vertex(name, (x, y))
            self._selected = None
            self._status_var.set(f"Вершину '{name}' додано. Клацніть вершину для ребра.")
        elif self._selected is None:
            self._selected = hit
            self._status_var.set(f"Обрано '{hit}'. Клацніть другу вершину.")
        elif self._selected == hit:
            # Подвійний клік по одній вершині — петля
            self._add_edge_dialog(hit)
        else:
            self._add_edge_dialog(hit)

        self._redraw()

    def _add_edge_dialog(self, target: str) -> None:
        ws = simpledialog.askstring(
            "Вага ребра",
            f"Вага ребра {self._selected} → {target}:",
            parent=self,
        )
        if ws is None:
            self._selected = None
            return
        try:
            w = float(ws.strip())
        except ValueError:
            messagebox.showerror("Помилка", f"'{ws}' не є числом!", parent=self)
            return
        self._graph.add_edge(self._selected, target, w)
        self._status_var.set(
            f"Ребро {self._selected}→{target} (вага={w:g}) додано.")
        self._selected = None

    def _undo(self) -> None:
        self._graph.remove_last_edge()
        self._status_var.set("Останнє ребро видалено.")
        self._redraw()

    def _clear(self) -> None:
        if messagebox.askyesno("Очистити", "Видалити весь граф?", parent=self):
            self._graph.clear()
            self._selected = None
            self._status_var.set("Граф очищено.")
            self._redraw()

    def _done(self) -> None:
        if len(self._graph.vertices) < 2:
            messagebox.showerror(
                "Помилка", "Потрібно щонайменше 2 вершини!", parent=self)
            return
        self._on_done(self._graph)
        self.destroy()

    # ── Малювання ──────────────────────────────────────────
    def _redraw(self) -> None:
        self._canvas.delete("all")
        self._canvas.configure(bg="white")
        self._draw_edges()
        self._draw_vertices()

    def _draw_edges(self) -> None:
        drawn = set()
        for u, v, w in self._graph.get_edges():
            if (u, v) in drawn:
                continue
            drawn.add((u, v))
            pu = self._graph.get_pos(u)
            pv = self._graph.get_pos(v)
            if not pu or not pv:
                continue
            x1, y1 = pu; x2, y2 = pv

            # Петля
            if u == v:
                r = VERTEX_RADIUS
                self._canvas.create_oval(
                    x1 - r, y1 - r * 3,
                    x1 + r, y1 - r,
                    outline="#333333", width=2, fill="")
                self._canvas.create_text(
                    x1 + r + 8, y1 - r * 2,
                    text=f"{w:g}", fill="#000000",
                    font=("Helvetica", 9, "bold"))
                continue

            d = math.hypot(x2 - x1, y2 - y1) or 1
            nx, ny = (x2 - x1) / d, (y2 - y1) / d
            self._canvas.create_line(
                x1 + nx * VERTEX_RADIUS, y1 + ny * VERTEX_RADIUS,
                x2 - nx * (VERTEX_RADIUS + 6), y2 - ny * (VERTEX_RADIUS + 6),
                fill="#333333", width=2,
                arrow=tk.LAST if self._directed else tk.NONE,
                arrowshape=(10, 12, 4),
            )
            self._canvas.create_text(
                (x1 + x2) / 2, (y1 + y2) / 2 - 12,
                text=f"{w:g}", fill="#000000",
                font=("Helvetica", 9, "bold"),
            )

    def _draw_vertices(self) -> None:
        for i, (name, pos) in enumerate(self._graph.vertices.items()):
            if not pos:
                continue
            x, y = pos
            color = VERTEX_COLORS[i % len(VERTEX_COLORS)]
            lw = 3 if name == self._selected else 1
            self._canvas.create_oval(
                x - VERTEX_RADIUS, y - VERTEX_RADIUS,
                x + VERTEX_RADIUS, y + VERTEX_RADIUS,
                fill=color, outline="#000000", width=lw,
            )
            self._canvas.create_text(
                x, y, text=name, fill="white",
                font=("Helvetica", 11, "bold"),
            )