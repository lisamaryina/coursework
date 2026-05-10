"""
visualizer.py — візуалізація графу та знайденого найкоротшого шляху.

Особливості:
  • Вершини з координатами відображаються на своїх позиціях
  • Вершини без координат розміщуються по колу
  • Знайдений шлях виділяється кольором та товщиною ліній
  • Збереження зображення у PNG та PS/PDF
"""

from __future__ import annotations
import math
from typing import List
import tkinter as tk
from tkinter import filedialog, messagebox

from graph import Graph

CANVAS_W = 750
CANVAS_H = 560
VERTEX_RADIUS = 22

COLOR_VERTEX = "#1a6aff"
COLOR_PATH   = "#cc0000"
COLOR_START  = "#1a8a1a"
COLOR_END    = "#cc5500"


class GraphVisualizer(tk.Toplevel):
    """
    Вікно візуалізації графу.
    Відповідає лише за відображення — не змінює граф.
    """

    def __init__(self, master: tk.Tk, graph: Graph,
                 path: List[str]) -> None:
        super().__init__(master)
        self.title("Візуалізація графу")
        self.resizable(True, True)

        self._graph: Graph = graph
        self._path: List[str] = path
        self._positions = self._compute_positions()

        self._build_ui()
        self.lift()

    # ── Обчислення позицій ─────────────────────────────────
    def _compute_positions(self) -> dict:
        positions = {}
        no_pos = [v for v in self._graph.vertices if not self._graph.get_pos(v)]
        positions.update({
            v: self._graph.get_pos(v)
            for v in self._graph.vertices if self._graph.get_pos(v)
        })
        n = len(no_pos)
        cx, cy = CANVAS_W / 2, CANVAS_H / 2
        r = min(cx, cy) * 0.74
        for i, v in enumerate(no_pos):
            angle = 2 * math.pi * i / n - math.pi / 2
            positions[v] = (cx + r * math.cos(angle), cy + r * math.sin(angle))
        return positions

    # ── Побудова UI ────────────────────────────────────────
    def _build_ui(self) -> None:
        self._canvas = tk.Canvas(
            self, width=CANVAS_W, height=CANVAS_H,
            bg="white", highlightthickness=1,
            highlightbackground="#aaaaaa",
        )
        self._canvas.pack(fill="both", expand=True, padx=10, pady=(10, 4))

        self._build_legend()
        self._build_info_label()
        self._build_save_button()
        self._draw()

    def _build_legend(self) -> None:
        frame = tk.Frame(self)
        frame.pack(fill="x", padx=10)
        for color, label in [
            (COLOR_VERTEX, "Вершина"),
            (COLOR_PATH,   "Шлях"),
            (COLOR_START,  "Початок"),
            (COLOR_END,    "Кінець"),
        ]:
            dot = tk.Canvas(frame, width=14, height=14,
                             bg="white", highlightthickness=0)
            dot.pack(side="left", padx=(4, 2))
            dot.create_oval(1, 1, 13, 13, fill=color, outline="")
            tk.Label(frame, text=label,
                      font=("Helvetica", 9)).pack(side="left", padx=(0, 12))

    def _build_info_label(self) -> None:
        if self._path:
            info = "Шлях: " + " → ".join(self._path)
        else:
            info = "Шлях не знайдено"
        tk.Label(self, text=info,
                  font=("Helvetica", 9, "italic"),
                  wraplength=CANVAS_W).pack(pady=(2, 4))

    def _build_save_button(self) -> None:
        tk.Button(self,
                  text="💾  Зберегти зображення як PNG",
                  font=("Helvetica", 10), padx=10, pady=4,
                  command=self._save_png,
                  ).pack(pady=(0, 8))

    # ── Збереження PNG ─────────────────────────────────────
    def _save_png(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("All files", "*.*")],
            title="Зберегти візуалізацію")
        if not path:
            return
        try:
            # Спочатку зберігаємо як PostScript, потім конвертуємо у PNG
            import os
            ps_path = path.replace(".png", "_tmp.ps")
            self._canvas.postscript(file=ps_path, colormode="color")

            try:
                from PIL import Image
                img = Image.open(ps_path)
                img.save(path, "PNG")
                os.remove(ps_path)
            except Exception:
                # Якщо PIL не може відкрити PS — спробуємо через ImageGrab
                os.remove(ps_path)
                self._save_png_grab(path)

            messagebox.showinfo("Збережено",
                                f"Зображення збережено:\n{path}")
        except Exception as e:
            messagebox.showerror("Помилка збереження", str(e))

    def _save_png_grab(self, path: str) -> None:
        """Альтернативний спосіб через скріншот canvas."""
        try:
            from PIL import ImageGrab
            # Отримати координати canvas на екрані
            self.update_idletasks()
            x = self._canvas.winfo_rootx()
            y = self._canvas.winfo_rooty()
            w = self._canvas.winfo_width()
            h = self._canvas.winfo_height()
            img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            img.save(path, "PNG")
        except Exception:
            # Останній варіант — зберегти як EPS (векторний)
            eps_path = path.replace(".png", ".eps")
            self._canvas.postscript(file=eps_path, colormode="color")
            messagebox.showinfo(
                "Збережено як EPS",
                f"PNG не вдалось створити.\n"
                f"Збережено як векторний EPS:\n{eps_path}\n\n"
                f"Відкрий у Preview або Illustrator.")

    # ── Малювання ──────────────────────────────────────────
    def _draw(self) -> None:
        c = self._canvas
        c.delete("all")
        c.configure(bg="white")

        path_edges = self._get_path_edges()
        self._draw_edges(path_edges)
        self._draw_vertices()

    def _get_path_edges(self) -> set:
        edges = set()
        for i in range(len(self._path) - 1):
            edges.add((self._path[i], self._path[i + 1]))
            if not self._graph.directed:
                edges.add((self._path[i + 1], self._path[i]))
        return edges

    def _draw_edges(self, path_edges: set) -> None:
        drawn = set()
        for u, v, w in self._graph.get_edges():
            if (u, v) in drawn:
                continue
            drawn.add((u, v))
            x1, y1 = self._positions[u]
            x2, y2 = self._positions[v]
            on_path = (u, v) in path_edges or (v, u) in path_edges
            color = COLOR_PATH if on_path else "#666666"
            width = 4 if on_path else 1.5
            vr = VERTEX_RADIUS

            # Петля (ребро вершини до себе)
            if u == v:
                self._draw_loop(x1, y1, w, color, width, on_path)
                continue

            d = math.hypot(x2 - x1, y2 - y1) or 1
            nx, ny = (x2 - x1) / d, (y2 - y1) / d
            self._canvas.create_line(
                x1 + nx * vr, y1 + ny * vr,
                x2 - nx * (vr + 4), y2 - ny * (vr + 4),
                fill=color, width=width,
                arrow=tk.LAST if self._graph.directed else tk.NONE,
                arrowshape=(10, 12, 4),
            )
            self._canvas.create_text(
                (x1 + x2) / 2, (y1 + y2) / 2 - 11,
                text=f"{w:g}",
                fill=COLOR_PATH if on_path else "#333333",
                font=("Helvetica", 9, "bold" if on_path else "normal"),
            )

    def _draw_loop(self, x: float, y: float, w: float,
                   color: str, width: float, on_path: bool) -> None:
        """Намалювати петлю — дугу від вершини до себе."""
        r = VERTEX_RADIUS
        # Малюємо овал над вершиною
        self._canvas.create_oval(
            x - r, y - r * 3,
            x + r, y - r,
            outline=color, width=width, fill=""
        )
        # Вага петлі
        self._canvas.create_text(
            x + r + 8, y - r * 2,
            text=f"{w:g}",
            fill=COLOR_PATH if on_path else "#333333",
            font=("Helvetica", 9, "bold" if on_path else "normal"),
        )

    def _draw_vertices(self) -> None:
        path_set = set(self._path) if self._path else set()
        for name, (x, y) in self._positions.items():
            if self._path and name == self._path[0]:
                color = COLOR_START
            elif self._path and name == self._path[-1]:
                color = COLOR_END
            elif name in path_set:
                color = COLOR_PATH
            else:
                color = COLOR_VERTEX
            vr = VERTEX_RADIUS
            self._canvas.create_oval(
                x - vr, y - vr, x + vr, y + vr,
                fill=color, outline="#000000", width=2,
            )
            self._canvas.create_text(
                x, y, text=name, fill="white",
                font=("Helvetica", 10, "bold"),
            )