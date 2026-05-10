"""
main.py — головне вікно програми.

Введення графу через матрицю суміжності або графічний редактор.
A* підтримує введення координат вершин для евристики.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Tuple
import tkinter as tk
from tkinter import messagebox, filedialog
import time

from graph import Graph
from algorithms import dijkstra, bellman_ford, astar
from graph_editor import GraphEditorWindow
from visualizer import GraphVisualizer


ALGO_NAMES = {
    "dijkstra":     "Дейкстри",
    "bellman_ford": "Беллмана-Форда",
    "astar":        "A*",
}

ALGO_COMPLEXITY = {
    "dijkstra": {
        "time":  "O((V + E) log V)",
        "space": "O(V)",
        "note":  "тільки невід'ємні ваги",
    },
    "bellman_ford": {
        "time":  "O(V · E)",
        "space": "O(V)",
        "note":  "допускає від'ємні ваги, виявляє від'ємні цикли",
    },
    "astar": {
        "time":  "O((V + E) log V) + O(V · E) для потенціалів",
        "space": "O(V)",
        "note":  "евристика h=0 або евклідова відстань",
    },
}

INSTRUCTIONS = "\n".join([
    "ІНСТРУКЦІЯ КОРИСТУВАЧА",
    "=" * 50,
    "",
    "КРОК 1. Оберіть тип графу:",
    "  - Неорієнтований або Орієнтований",
    "",
    "КРОК 2. Введіть граф одним зі способів:",
    "",
    "  [ Матриця суміжності ]",
    "  - Введіть вершини через пробіл (напр.: A B C)",
    "  - Натисніть 'Побудувати матрицю'",
    "  - Заповніть комірки: вага ребра або 0/порожньо",
    "    якщо ребра немає",
    "  - Натисніть 'Підтвердити'",
    "",
    "  [ Графічне введення ]",
    "  - Клік на вільному місці = нова вершина",
    "  - Клік по 1-й, потім 2-й вершині = ребро",
    "  - Кнопка 'Готово' = зберегти граф",
    "",
    "КРОК 3. Задайте початкову та кінцеву вершини.",
    "",
    "КРОК 4. Оберіть алгоритм:",
    "  - Дейкстри       : тільки невід'ємні ваги",
    "  - Беллмана-Форда : допускає від'ємні ваги",
    "  - A*             : від'ємні ваги тільки для",
    "                     орієнтованого графу",
    "",
    "  Для A* можна задати координати вершин —",
    "  тоді евристика = евклідова відстань.",
    "  Без координат евристика = 0.",
    "",
    "КРОК 5. Натисніть 'Знайти найкоротший шлях'.",
    "",
    "КРОК 6. Результат у полі нижче.",
    "  - 'Зберегти результат' — зберегти у .txt",
    "  - 'Візуалізувати граф' — відкрити вікно графу",
    "",
    "=" * 50,
])


class MainApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Знаходження найкоротшого шляху")
        self.minsize(700, 580)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.graph: Optional[Graph] = None
        self._last_path: List[str] = []
        self._astar_coords: Dict[str, Tuple[float, float]] = {}

        self._build_ui()

    # ══════════════════════════════════════════════
    #  Побудова інтерфейсу
    # ══════════════════════════════════════════════
    def _build_ui(self) -> None:
        main = tk.Frame(self)
        main.grid(row=0, column=0, sticky="nsew", padx=24, pady=12)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(7, weight=1)

        # Заголовок
        hdr = tk.Frame(main)
        hdr.grid(row=0, column=0, sticky="ew", pady=(4, 10))
        hdr.columnconfigure(0, weight=1)
        tk.Label(hdr, text="Знаходження найкоротшого шляху",
                 font=("Helvetica", 16, "bold")).grid(row=0, column=0)
        tk.Label(hdr, text="Алгоритми: Дейкстри  ·  Беллмана-Форда  ·  A*",
                 font=("Helvetica", 11)).grid(row=1, column=0, pady=(2, 0))

        self._divider(main, row=1)

        # Блок 1: введення
        f1 = tk.LabelFrame(main, text="  1. Введення графу  ",
                            font=("Helvetica", 11, "bold"), padx=16, pady=12)
        f1.grid(row=2, column=0, sticky="ew", pady=4)
        f1.columnconfigure(1, weight=1)
        self._build_input_block(f1)

        self._divider(main, row=3)

        # Блок 2: пошук
        f2 = tk.LabelFrame(main, text="  2. Параметри пошуку  ",
                            font=("Helvetica", 11, "bold"), padx=16, pady=12)
        f2.grid(row=4, column=0, sticky="ew", pady=4)
        f2.columnconfigure(0, weight=1)
        self._build_search_block(f2)

        # Кнопка запуску
        tk.Button(main, text="▶   Знайти найкоротший шлях",
                  font=("Helvetica", 13, "bold"), pady=10,
                  command=self._run_algorithm,
                  ).grid(row=5, column=0, sticky="ew", pady=10)

        self._divider(main, row=6)

        # Блок 3: результат
        f3 = tk.LabelFrame(main, text="  3. Результат  ",
                            font=("Helvetica", 11, "bold"), padx=16, pady=12)
        f3.grid(row=7, column=0, sticky="nsew", pady=4)
        f3.columnconfigure(0, weight=1)
        f3.rowconfigure(0, weight=1)
        main.rowconfigure(7, weight=1)

        self._result_text = tk.Text(
            f3, state="disabled",
            font=("Courier", 11), relief="solid", bd=1, height=8)
        self._result_text.grid(row=0, column=0, sticky="nsew")
        sb = tk.Scrollbar(f3, command=self._result_text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._result_text.configure(yscrollcommand=sb.set)

        # Нижні кнопки
        bf = tk.Frame(main)
        bf.grid(row=8, column=0, sticky="ew", pady=(6, 4))
        bf.columnconfigure(2, weight=1)
        tk.Button(bf, text="Зберегти результат",
                  font=("Helvetica", 10), padx=10,
                  command=self._save_result).grid(row=0, column=0, sticky="w")
        tk.Button(bf, text="Зберегти граф",
                  font=("Helvetica", 10), padx=10,
                  command=self._save_graph).grid(row=0, column=1, sticky="w", padx=6)
        tk.Button(bf, text="Візуалізувати граф",
                  font=("Helvetica", 10), padx=10,
                  command=self._open_visualizer).grid(row=0, column=2, sticky="w", padx=6)
        tk.Button(bf, text="Інструкція",
                  font=("Helvetica", 10), padx=10,
                  command=self._show_instructions).grid(row=0, column=3, sticky="e")

    def _divider(self, parent: tk.Frame, row: int) -> None:
        tk.Frame(parent, height=1, bg="#cccccc").grid(
            row=row, column=0, sticky="ew", pady=2)

    def _build_input_block(self, parent: tk.Frame) -> None:
        tk.Label(parent, text="Тип графу:",
                 font=("Helvetica", 11)).grid(row=0, column=0, sticky="w")
        type_frame = tk.Frame(parent)
        type_frame.grid(row=0, column=1, sticky="w", padx=(12, 0))
        self._gtype = tk.StringVar(value="undirected")
        tk.Radiobutton(type_frame, text="Неорієнтований",
                       variable=self._gtype, value="undirected",
                       font=("Helvetica", 11)).pack(side="left")
        tk.Radiobutton(type_frame, text="Орієнтований",
                       variable=self._gtype, value="directed",
                       font=("Helvetica", 11)).pack(side="left", padx=(16, 0))

        tk.Label(parent, text="Спосіб введення:",
                 font=("Helvetica", 11)).grid(row=1, column=0, sticky="w", pady=(10, 0))
        btn_frame = tk.Frame(parent)
        btn_frame.grid(row=1, column=1, sticky="w", padx=(12, 0), pady=(10, 0))
        tk.Button(btn_frame, text="   Текстове введення   ",
                  font=("Helvetica", 11), padx=6,
                  command=self._open_text_input).pack(side="left")
        tk.Button(btn_frame, text="   Графічне введення   ",
                  font=("Helvetica", 11), padx=6,
                  command=self._open_graph_editor).pack(side="left", padx=(12, 0))

        self._lbl_graph_status = tk.Label(
            parent, text="Граф не задано", fg="red",
            font=("Helvetica", 10, "italic"))
        self._lbl_graph_status.grid(row=2, column=0, columnspan=2,
                                    sticky="w", pady=(8, 0))

    def _build_search_block(self, parent: tk.Frame) -> None:
        nodes_frame = tk.Frame(parent)
        nodes_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tk.Label(nodes_frame, text="Початкова вершина:",
                 font=("Helvetica", 11)).grid(row=0, column=0, sticky="w")
        self._entry_start = tk.Entry(nodes_frame, width=8, font=("Helvetica", 12))
        self._entry_start.grid(row=0, column=1, sticky="w", padx=(10, 30))
        tk.Label(nodes_frame, text="Кінцева вершина:",
                 font=("Helvetica", 11)).grid(row=0, column=2, sticky="w")
        self._entry_end = tk.Entry(nodes_frame, width=8, font=("Helvetica", 12))
        self._entry_end.grid(row=0, column=3, sticky="w", padx=(10, 0))

        algo_frame = tk.Frame(parent)
        algo_frame.grid(row=1, column=0, sticky="ew")
        tk.Label(algo_frame, text="Алгоритм:",
                 font=("Helvetica", 11)).pack(side="left")
        self._algo_var = tk.StringVar(value="dijkstra")
        for label, value in [("Дейкстри", "dijkstra"),
                              ("Беллмана-Форда", "bellman_ford"),
                              ("A*", "astar")]:
            tk.Radiobutton(algo_frame, text=label,
                           variable=self._algo_var, value=value,
                           font=("Helvetica", 11),
                           command=self._on_algo_change).pack(side="left", padx=(14, 0))

        # Кнопка координат для A* (спочатку прихована)
        self._coords_frame = tk.Frame(parent)
        self._coords_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self._btn_coords = tk.Button(
            self._coords_frame,
            text="📍  Задати координати вершин для евристики (необов'язково)",
            font=("Helvetica", 10), padx=6,
            command=self._open_coords_input)
        self._btn_coords.pack(side="left")
        self._lbl_coords_status = tk.Label(
            self._coords_frame,
            text="", font=("Helvetica", 9, "italic"), fg="#555555")
        self._lbl_coords_status.pack(side="left", padx=(10, 0))
        self._coords_frame.grid_remove()  # прихована до вибору A*

    def _on_algo_change(self) -> None:
        if self._algo_var.get() == "astar":
            self._coords_frame.grid()
        else:
            self._coords_frame.grid_remove()

    # ══════════════════════════════════════════════
    #  Введення графу
    # ══════════════════════════════════════════════
    def _is_directed(self) -> bool:
        return self._gtype.get() == "directed"

    def _open_text_input(self) -> None:
        TextInputWindow(self, directed=self._is_directed(),
                        on_done=self._receive_graph)

    def _open_graph_editor(self) -> None:
        GraphEditorWindow(self, directed=self._is_directed(),
                          on_done=self._receive_graph)

    def _receive_graph(self, graph: Graph) -> None:
        self.graph = graph
        self._astar_coords = {}
        self._lbl_coords_status.config(text="")
        self._update_graph_status()

    def _update_graph_status(self) -> None:
        if self.graph:
            d = "орієнтований" if self.graph.directed else "неорієнтований"
            self._lbl_graph_status.config(
                text=(f"✔  Граф задано: {len(self.graph.vertices)} вершин, "
                      f"{self.graph.edge_count()} ребер ({d})"),
                fg="green")
        else:
            self._lbl_graph_status.config(text="Граф не задано", fg="red")

    # ══════════════════════════════════════════════
    #  Координати для A*
    # ══════════════════════════════════════════════
    def _open_coords_input(self) -> None:
        if not self.graph:
            messagebox.showerror("Помилка", "Спочатку введіть граф!")
            return
        CoordsInputWindow(self, vertices=list(self.graph.vertices.keys()),
                          current=self._astar_coords,
                          on_done=self._receive_coords)

    def _receive_coords(self, coords: Dict[str, Tuple[float, float]]) -> None:
        self._astar_coords = coords
        if coords:
            self._lbl_coords_status.config(
                text=f"✔ Координати задано для {len(coords)} вершин", fg="green")
        else:
            self._lbl_coords_status.config(text="", fg="#555555")

    # ══════════════════════════════════════════════
    #  Алгоритм
    # ══════════════════════════════════════════════
    def _run_algorithm(self) -> None:
        if not self._validate_inputs():
            return
        algo  = self._algo_var.get()
        start = self._entry_start.get().strip()
        end   = self._entry_end.get().strip()

        if algo == "dijkstra" and self.graph.has_negative_weights():
            messagebox.showerror(
                "Помилка",
                "Алгоритм Дейкстри не підтримує від'ємні ваги.\n"
                "Оберіть Беллмана-Форда або A*.")
            return

        t0 = time.perf_counter()
        try:
            if algo == "dijkstra":
                path, dist = dijkstra(self.graph, start, end)
            elif algo == "bellman_ford":
                path, dist = bellman_ford(self.graph, start, end)
            else:
                coords = self._astar_coords if self._astar_coords else None
                path, dist = astar(self.graph, start, end, coords=coords)
        except ValueError as e:
            messagebox.showerror("Помилка виконання", str(e))
            return
        elapsed = time.perf_counter() - t0

        self._last_path = path
        self._display_result(start, end, algo, path, dist, elapsed)

    def _validate_inputs(self) -> bool:
        if not self.graph:
            messagebox.showerror("Помилка", "Спочатку введіть граф!")
            return False
        start = self._entry_start.get().strip()
        end   = self._entry_end.get().strip()
        if not start or not end:
            messagebox.showerror("Помилка", "Введіть початкову та кінцеву вершини!")
            return False
        if start not in self.graph.vertices:
            messagebox.showerror("Помилка", f"Вершина '{start}' не існує у графі!")
            return False
        if end not in self.graph.vertices:
            messagebox.showerror("Помилка", f"Вершина '{end}' не існує у графі!")
            return False
        return True

    def _display_result(self, start: str, end: str, algo: str,
                        path: List[str], dist: float, elapsed: float) -> None:
        sep = "-" * 48
        lines = [f"Алгоритм : {ALGO_NAMES[algo]}"]
        if algo == "astar" and self._astar_coords:
            lines.append("Евристика: евклідова відстань")
        elif algo == "astar":
            lines.append("Евристика: h = 0 (координати не задано)")
        lines += [f"Початок  : {start}     Кінець : {end}", sep]
        if path:
            lines += [f"Шлях     : {' → '.join(path)}",
                      f"Довжина  : {dist:.15f}"]
        else:
            lines.append(f"Шляху між '{start}' та '{end}' не існує.")
        lines += [sep,
                  f"Час виконання : {elapsed * 1000:.6f} мс",
                  f"Вершин: {len(self.graph.vertices)}   "
                  f"Ребер: {self.graph.edge_count()}"]
        self._result_text.configure(state="normal")
        self._result_text.delete("1.0", "end")
        self._result_text.insert("1.0", "\n".join(lines))
        self._result_text.configure(state="disabled")

    # ══════════════════════════════════════════════
    #  Збереження та візуалізація
    # ══════════════════════════════════════════════
    def _save_result(self) -> None:
        content = self._result_text.get("1.0", "end").strip()
        if not content:
            messagebox.showinfo("", "Немає результату для збереження.")
            return
        if not self.graph:
            messagebox.showinfo("", "Немає графу для збереження.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Зберегти результат")
        if not path:
            return

        # Зберегти результат разом з інформацією про граф
        if self.graph:
            graph_info = self._get_graph_info()
            full_content = content + "\n\n" + graph_info
        else:
            full_content = content

        with open(path, "w", encoding="utf-8") as f:
            f.write(full_content)
        messagebox.showinfo("Збережено", f"Файл збережено:\n{path}")

    def _get_graph_info(self) -> str:
        """Сформувати текстовий опис введеного графу."""
        d = "орієнтований" if self.graph.directed else "неорієнтований"
        lines = [
            "=" * 48,
            "ВВЕДЕНИЙ ГРАФ",
            "=" * 48,
            f"Тип графу  : {d}",
            f"Вершини    : {' '.join(self.graph.vertices.keys())}",
            f"Вершин     : {len(self.graph.vertices)}",
            f"Ребер      : {self.graph.edge_count()}",
            "",
            "Ребра (звідки  куди  вага):",
        ]
        for u, v, w in self.graph.get_edges():
            lines.append(f"  {u}  ->  {v}  :  {w}")
        return "\n".join(lines)

    def _save_graph(self) -> None:
        """Зберегти введений граф у текстовий файл."""
        if not self.graph:
            messagebox.showinfo("", "Спочатку введіть граф!")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Зберегти граф")
        if not path:
            return
        lines = []
        d = "орієнтований" if self.graph.directed else "неорієнтований"
        lines.append(f"Тип графу: {d}")
        lines.append(f"Вершини: {' '.join(self.graph.vertices.keys())}")
        lines.append(f"Кількість вершин: {len(self.graph.vertices)}")
        lines.append(f"Кількість ребер: {self.graph.edge_count()}")
        lines.append("")
        lines.append("Ребра (звідки  куди  вага):")
        for u, v, w in self.graph.get_edges():
            lines.append(f"  {u}  {v}  {w}")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        messagebox.showinfo("Збережено", f"Граф збережено:\n{path}")

    def _open_visualizer(self) -> None:
        if not self.graph:
            messagebox.showerror("Помилка", "Спочатку введіть граф!")
            return
        GraphVisualizer(self, self.graph, self._last_path)

    def _show_instructions(self) -> None:
        InstructionsWindow(self)


# ══════════════════════════════════════════════════════
#  Вікно текстового введення
# ══════════════════════════════════════════════════════
class TextInputWindow(tk.Toplevel):
    """Введення графу через список ребер."""

    def __init__(self, master: tk.Tk, directed: bool,
                 on_done: callable) -> None:
        super().__init__(master)
        self.title("Текстове введення графу")
        self.minsize(500, 420)
        self.resizable(True, True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._directed = directed
        self._on_done = on_done
        self.lift()
        self.focus_force()
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Вершини (через пробіл):",
                 font=("Helvetica", 11)).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 2))
        self._entry_vertices = tk.Entry(self, font=("Helvetica", 11))
        self._entry_vertices.grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self._entry_vertices.focus_set()

        tk.Label(self, text="Ребра (кожне на новому рядку:  звідки  куди  вага):",
                 font=("Helvetica", 11)).grid(
            row=2, column=0, sticky="w", padx=16)

        edge_frame = tk.Frame(self)
        edge_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 4))
        edge_frame.columnconfigure(0, weight=1)
        edge_frame.rowconfigure(0, weight=1)

        sb = tk.Scrollbar(edge_frame)
        sb.grid(row=0, column=1, sticky="ns")
        self._text_edges = tk.Text(edge_frame, font=("Courier", 11),
                                   yscrollcommand=sb.set, height=8)
        self._text_edges.grid(row=0, column=0, sticky="nsew")
        sb.config(command=self._text_edges.yview)

        tk.Label(self, text="Приклад: A B 5   або   1 2 -3.5",
                 font=("Helvetica", 10, "italic")).grid(
            row=4, column=0, sticky="w", padx=16)

        tk.Button(self, text="Підтвердити", command=self._confirm,
                  font=("Helvetica", 12), pady=8).grid(
            row=5, column=0, pady=12)

    def _confirm(self) -> None:
        raw_v = self._entry_vertices.get().strip()
        if not raw_v:
            messagebox.showerror("Помилка", "Введіть вершини!", parent=self)
            return
        vertices = [v.strip() for v in raw_v.replace(",", " ").split()
                    if v.strip()]
        if len(vertices) != len(set(vertices)):
            messagebox.showerror("Помилка", "Вершини мають бути унікальними!",
                                 parent=self)
            return
        g = Graph(directed=self._directed)
        for v in vertices:
            g.add_vertex(v)
        for line in self._text_edges.get("1.0", "end").strip().splitlines():
            parts = line.strip().split()
            if not parts:
                continue
            if len(parts) != 3:
                messagebox.showerror(
                    "Помилка", f"Рядок: '{line}'\nФормат: звідки куди вага",
                    parent=self)
                return
            u, v, ws = parts
            if u not in g.vertices:
                messagebox.showerror("Помилка", f"Вершина '{u}' не існує.",
                                     parent=self)
                return
            if v not in g.vertices:
                messagebox.showerror("Помилка", f"Вершина '{v}' не існує.",
                                     parent=self)
                return
            try:
                w = float(ws)
            except ValueError:
                messagebox.showerror("Помилка", f"'{ws}' не є числом!",
                                     parent=self)
                return
            import math
            if math.isinf(w) or math.isnan(w):
                messagebox.showerror("Помилка",
                    f"Вага '{ws}' виходить за межі допустимих значень.",
                    parent=self)
                return
            # Перевірка: ненульове значення не може бути меншим за 1e-15 за модулем
            if w != 0 and abs(w) < 1e-15:
                messagebox.showerror("Помилка",
                    f"Вага '{ws}' занадто мала.\n"
                    f"Мінімально допустиме значення за модулем: 1e-15",
                    parent=self)
                return
            # Перевірка кількості знаків після коми (лише для звичайного запису)
            ws_clean = ws.lstrip('-')
            if '.' in ws_clean and 'e' not in ws_clean.lower():
                decimal_part = ws_clean.split('.')[1]
                if len(decimal_part) > 15:
                    messagebox.showerror("Помилка",
                        f"Вага '{ws}' має більше 15 знаків після коми.\n"
                        f"Максимально допустимо: 15 знаків після коми.",
                        parent=self)
                    return
            g.add_edge(u, v, w)
        self._on_done(g)
        self.destroy()
        messagebox.showinfo(
            "Готово",
            f"Граф задано: {len(g.vertices)} вершин, {g.edge_count()} ребер.")


# ══════════════════════════════════════════════════════
#  Вікно координат для A*
# ══════════════════════════════════════════════════════
class CoordsInputWindow(tk.Toplevel):
    """Введення координат вершин для евристики A*."""

    def __init__(self, master: tk.Tk, vertices: List[str],
                 current: Dict[str, Tuple[float, float]],
                 on_done: callable) -> None:
        super().__init__(master)
        self.title("Координати вершин для A*")
        self.resizable(False, False)
        self._vertices = vertices
        self._current = current
        self._on_done = on_done
        self._x_entries: Dict[str, tk.Entry] = {}
        self._y_entries: Dict[str, tk.Entry] = {}
        self.lift()
        self.focus_force()
        self._build()

    def _build(self) -> None:
        tk.Label(self,
                 text="Задайте координати вершин для евклідової евристики.\n"
                      "Залиште порожнім — евристика h=0 для цієї вершини.",
                 font=("Helvetica", 10, "italic"),
                 justify="left").pack(padx=16, pady=(12, 8))

        # Заголовок
        hdr = tk.Frame(self)
        hdr.pack(fill="x", padx=16)
        tk.Label(hdr, text="Вершина", width=10,
                 font=("Helvetica", 10, "bold")).pack(side="left")
        tk.Label(hdr, text="X", width=12,
                 font=("Helvetica", 10, "bold")).pack(side="left", padx=(0, 4))
        tk.Label(hdr, text="Y", width=12,
                 font=("Helvetica", 10, "bold")).pack(side="left")

        # Рядки для кожної вершини
        for v in self._vertices:
            row = tk.Frame(self)
            row.pack(fill="x", padx=16, pady=2)
            tk.Label(row, text=v, width=10,
                     font=("Helvetica", 11, "bold")).pack(side="left")
            ex = tk.Entry(row, width=12, font=("Helvetica", 11),
                           justify="center")
            ex.pack(side="left", padx=(0, 4))
            ey = tk.Entry(row, width=12, font=("Helvetica", 11),
                           justify="center")
            ey.pack(side="left")
            # Заповнити поточні значення якщо є
            if v in self._current:
                ex.insert(0, str(self._current[v][0]))
                ey.insert(0, str(self._current[v][1]))
            self._x_entries[v] = ex
            self._y_entries[v] = ey

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=14)
        tk.Button(btn_frame, text="Підтвердити",
                  font=("Helvetica", 11), padx=10,
                  command=self._confirm).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Скинути все",
                  font=("Helvetica", 11), padx=10,
                  command=self._clear).pack(side="left", padx=6)

    def _confirm(self) -> None:
        coords: Dict[str, Tuple[float, float]] = {}
        for v in self._vertices:
            rx = self._x_entries[v].get().strip()
            ry = self._y_entries[v].get().strip()
            if not rx and not ry:
                continue
            try:
                x = float(rx)
                y = float(ry)
            except ValueError:
                messagebox.showerror(
                    "Помилка",
                    f"Некоректні координати для вершини '{v}'.\n"
                    "Введіть числа або залиште поля порожніми.",
                    parent=self)
                return
            coords[v] = (x, y)
        self._on_done(coords)
        self.destroy()

    def _clear(self) -> None:
        for v in self._vertices:
            self._x_entries[v].delete(0, "end")
            self._y_entries[v].delete(0, "end")


# ══════════════════════════════════════════════════════
#  Вікно інструкції
# ══════════════════════════════════════════════════════
class InstructionsWindow(tk.Toplevel):
    STEPS = [
        ("1. Тип графу",
         "Оберіть тип:\n"
         "  • Неорієнтований — ребра двосторонні\n"
         "  • Орієнтований   — ребра мають напрямок"),

        ("2. Введення графу",
         "[ Текстове введення ]\n"
         "  • Вершини: через пробіл, напр.: A B C D\n"
         "  • Ребра: кожне на новому рядку:\n"
         "    звідки  куди  вага   (напр.: A B 5)\n\n"
         "[ Графічне введення ]\n"
         "  • Клік на вільному місці = нова вершина\n"
         "  • Клік по 1-й, потім 2-й вершині = ребро\n"
         "  • 'Готово' = зберегти граф"),

        ("3. Вершини пошуку",
         "Введіть назви початкової та кінцевої вершин."),

        ("4. Алгоритм",
         "  • Дейкстри       — тільки невід'ємні ваги\n"
         "  • Беллмана-Форда — допускає від'ємні ваги\n"
         "  • A*             — від'ємні ваги тільки\n"
         "                     для орієнтованого графу\n\n"
         "Для A* можна задати координати вершин.\n"
         "Тоді евристика = евклідова відстань до кінця.\n"
         "Без координат — h = 0."),

        ("5. Запуск",
         "Натисніть «▶  Знайти найкоротший шлях»."),

        ("6. Результат",
         "  • 'Зберегти результат' — зберегти у .txt\n"
         "  • 'Візуалізувати граф' — відкрити вікно"),
    ]

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.title("Інструкція користувача")
        self.minsize(520, 480)
        self.resizable(True, True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.lift()
        self.focus_force()
        self._build()

    def _build(self) -> None:
        outer = tk.Frame(self)
        outer.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        canvas = tk.Canvas(outer, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")
        canvas.grid(row=0, column=0, sticky="nsew")

        inner = tk.Frame(canvas)
        inner.columnconfigure(0, weight=1)
        canvas.create_window((0, 0), window=inner, anchor="nw")

        tk.Label(inner, text="Інструкція користувача",
                 font=("Helvetica", 15, "bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        tk.Frame(inner, height=2, bg="#4299e1").grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 12))

        for i, (title, body) in enumerate(self.STEPS):
            block = tk.Frame(inner)
            block.grid(row=i + 2, column=0, sticky="ew", padx=16, pady=(0, 10))
            block.columnconfigure(0, weight=1)
            tk.Label(block, text=title, font=("Helvetica", 12, "bold"),
                     anchor="w").grid(row=0, column=0, sticky="ew")
            tk.Frame(block, height=1, bg="#dddddd").grid(
                row=1, column=0, sticky="ew", pady=(2, 6))
            tk.Label(block, text=body, font=("Helvetica", 11),
                     justify="left", anchor="w",
                     wraplength=460).grid(row=2, column=0, sticky="w")

        inner.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.bind("<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def _scroll(event):
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass
        self._scroll_binding = canvas.bind_all("<MouseWheel>", _scroll)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self) -> None:
        try:
            self.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
        self.destroy()

        tk.Button(self, text="Закрити", command=self.destroy,
                  font=("Helvetica", 11), padx=20, pady=4,
                  ).grid(row=1, column=0, pady=(0, 12))


if __name__ == "__main__":
    MainApp().mainloop()