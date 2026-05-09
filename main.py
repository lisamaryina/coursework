"""
main.py — головне вікно програми.
"""

from __future__ import annotations
from typing import Optional, List
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

INSTRUCTIONS = "\n".join([
    "ІНСТРУКЦІЯ КОРИСТУВАЧА",
    "=" * 50,
    "",
    "КРОК 1. Оберіть тип графу:",
    "  - Неорієнтований або Орієнтований",
    "",
    "КРОК 2. Введіть граф одним зі способів:",
    "",
    "  [ Текстове введення ]",
    "  - Вершини: через пробіл, напр.:  A B C D",
    "  - Ребра: кожне на новому рядку:",
    "    звідки  куди  вага   (напр.: A B 5)",
    "",
    "  [ Графічне введення ]",
    "  - Клік на вільному місці = нова вершина",
    "  - Клік по 1-й, потім 2-й вершині = ребро",
    "    (введіть вагу у вікні що зявиться)",
    "  - Кнопка 'Відмінити останнє ребро' = скасувати",
    "  - Кнопка 'Готово' = зберегти граф",
    "",
    "КРОК 3. Задайте початкову та кінцеву вершини.",
    "",
    "КРОК 4. Оберіть алгоритм:",
    "  - Дейкстри       : тільки невід'ємні ваги",
    "  - Беллмана-Форда : допускає від'ємні ваги",
    "  - A*             : тільки невід'ємні ваги",
    "",
    "КРОК 5. Натисніть 'Знайти найкоротший шлях'.",
    "",
    "КРОК 6. Результат відображається у полі нижче.",
    "  - 'Зберегти результат' — зберегти у .txt файл",
    "  - 'Візуалізувати граф' — відкрити вікно графу",
    "",
    "=" * 50,
])


class MainApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Знаходження найкоротшого шляху")
        self.minsize(700, 600)

        # Розтягування головної колонки
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.graph: Optional[Graph] = None
        self._last_path: List[str] = []

        self._build_ui()

    # ══════════════════════════════════════════════
    #  Побудова інтерфейсу
    # ══════════════════════════════════════════════
    def _build_ui(self) -> None:
        # Головний контейнер — grid для правильного розтягування
        main = tk.Frame(self)
        main.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(4, weight=1)  # рядок з результатом розтягується

        # ── Заголовок
        hdr = tk.Frame(main)
        hdr.grid(row=0, column=0, sticky="ew", pady=(4, 8))
        hdr.columnconfigure(0, weight=1)
        tk.Label(hdr, text="Знаходження найкоротшого шляху",
                 font=("Helvetica", 16, "bold")).grid(row=0, column=0)
        tk.Label(hdr, text="Алгоритми: Дейкстри  ·  Беллмана-Форда  ·  A*",
                 font=("Helvetica", 11)).grid(row=1, column=0, pady=(2, 0))

        self._divider(main, row=1)

        # ── Блок 1: введення
        f1 = tk.LabelFrame(main, text="  1. Введення графу  ",
                            font=("Helvetica", 11, "bold"),
                            padx=16, pady=12)
        f1.grid(row=2, column=0, sticky="ew", pady=4)
        f1.columnconfigure(1, weight=1)
        self._build_input_block(f1)

        self._divider(main, row=3)

        # ── Блок 2: пошук
        f2 = tk.LabelFrame(main, text="  2. Параметри пошуку  ",
                            font=("Helvetica", 11, "bold"),
                            padx=16, pady=12)
        f2.grid(row=4, column=0, sticky="ew", pady=4)
        f2.columnconfigure(0, weight=1)
        self._build_search_block(f2)

        # ── Кнопка запуску
        tk.Button(main, text="▶   Знайти найкоротший шлях",
                   font=("Helvetica", 13, "bold"), pady=10,
                   command=self._run_algorithm,
                   ).grid(row=5, column=0, sticky="ew", pady=10)

        self._divider(main, row=6)

        # ── Блок 3: результат (розтягується)
        f3 = tk.LabelFrame(main, text="  3. Результат  ",
                            font=("Helvetica", 11, "bold"),
                            padx=16, pady=12)
        f3.grid(row=7, column=0, sticky="nsew", pady=4)
        f3.columnconfigure(0, weight=1)
        f3.rowconfigure(0, weight=1)
        main.rowconfigure(7, weight=1)

        self._result_text = tk.Text(
            f3, state="disabled",
            font=("Courier", 11), relief="solid", bd=1,
            height=8,
        )
        self._result_text.grid(row=0, column=0, sticky="nsew")
        sb = tk.Scrollbar(f3, command=self._result_text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._result_text.configure(yscrollcommand=sb.set)

        # ── Нижні кнопки
        bf = tk.Frame(main)
        bf.grid(row=8, column=0, sticky="ew", pady=(6, 4))
        bf.columnconfigure(1, weight=1)
        tk.Button(bf, text="Зберегти результат",
                   font=("Helvetica", 10), padx=10,
                   command=self._save_result).grid(row=0, column=0, sticky="w")
        tk.Button(bf, text="Візуалізувати граф",
                   font=("Helvetica", 10), padx=10,
                   command=self._open_visualizer).grid(row=0, column=1, sticky="w", padx=10)
        tk.Button(bf, text="Інструкція",
                   font=("Helvetica", 10), padx=10,
                   command=self._show_instructions).grid(row=0, column=2, sticky="e")

    def _divider(self, parent: tk.Frame, row: int) -> None:
        tk.Frame(parent, height=1, bg="#cccccc").grid(
            row=row, column=0, sticky="ew", pady=2)

    def _build_input_block(self, parent: tk.Frame) -> None:
        # Тип графу
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

        # Кнопки введення
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

        # Статус
        self._lbl_graph_status = tk.Label(
            parent, text="Граф не задано", fg="red",
            font=("Helvetica", 10, "italic"))
        self._lbl_graph_status.grid(row=2, column=0, columnspan=2,
                                     sticky="w", pady=(8, 0))

    def _build_search_block(self, parent: tk.Frame) -> None:
        # Вершини
        nodes_frame = tk.Frame(parent)
        nodes_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        nodes_frame.columnconfigure(1, weight=0)
        nodes_frame.columnconfigure(3, weight=0)

        tk.Label(nodes_frame, text="Початкова вершина:",
                  font=("Helvetica", 11)).grid(row=0, column=0, sticky="w")
        self._entry_start = tk.Entry(nodes_frame, width=8, font=("Helvetica", 12))
        self._entry_start.grid(row=0, column=1, sticky="w", padx=(10, 30))

        tk.Label(nodes_frame, text="Кінцева вершина:",
                  font=("Helvetica", 11)).grid(row=0, column=2, sticky="w")
        self._entry_end = tk.Entry(nodes_frame, width=8, font=("Helvetica", 12))
        self._entry_end.grid(row=0, column=3, sticky="w", padx=(10, 0))

        # Алгоритм
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
                            font=("Helvetica", 11)).pack(side="left", padx=(14, 0))

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
    #  Алгоритм
    # ══════════════════════════════════════════════
    def _run_algorithm(self) -> None:
        if not self._validate_inputs():
            return
        algo  = self._algo_var.get()
        start = self._entry_start.get().strip()
        end   = self._entry_end.get().strip()

        if algo in ("dijkstra", "astar") and self.graph.has_negative_weights():
            messagebox.showerror(
                "Помилка",
                f"Алгоритм {ALGO_NAMES[algo]} не підтримує від'ємні ваги.\n"
                "Оберіть алгоритм Беллмана-Форда.")
            return

        t0 = time.perf_counter()
        try:
            if algo == "dijkstra":
                path, dist = dijkstra(self.graph, start, end)
            elif algo == "bellman_ford":
                path, dist = bellman_ford(self.graph, start, end)
            else:
                path, dist = astar(self.graph, start, end)
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
        lines = [
            f"Алгоритм : {ALGO_NAMES[algo]}",
            f"Початок  : {start}     Кінець : {end}",
            sep,
        ]
        if path:
            lines += [
                f"Шлях     : {' → '.join(path)}",
                f"Довжина  : {dist:.4f}",
            ]
        else:
            lines.append(f"Шляху між '{start}' та '{end}' не існує.")
        lines += [
            sep,
            f"Час виконання : {elapsed * 1000:.4f} мс",
            f"Вершин: {len(self.graph.vertices)}   Ребер: {self.graph.edge_count()}",
        ]
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
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Зберегти результат")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Збережено", f"Файл збережено:\n{path}")

    def _open_visualizer(self) -> None:
        if not self.graph:
            messagebox.showerror("Помилка", "Спочатку введіть граф!")
            return
        GraphVisualizer(self, self.graph, self._last_path)

    def _show_instructions(self) -> None:
        InstructionsWindow(self)


# ══════════════════════════════════════════════════════
#  Допоміжні вікна
# ══════════════════════════════════════════════════════
class InstructionsWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.title("Інструкція користувача")
        self.geometry("700x500")
        self.resizable(False, False)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._build()

    def _build(self) -> None:
        frame = tk.Frame(self, padx=20, pady=20)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        instruction_text = (
            "ІНСТРУКЦІЯ КОРИСТУВАЧА\n\n"
            "1. Оберіть тип графу: неорієнтований або орієнтований.\n\n"
            "2. Введіть граф одним зі способів:\n"
            "• Текстове введення: задайте вершини через пробіл, а ребра — кожне з нового рядка у форматі: звідки куди вага.\n"
            "• Графічне введення: клік на вільному місці створює вершину, клік по двох вершинах створює ребро.\n\n"
            "3. Введіть початкову та кінцеву вершини.\n\n"
            "4. Оберіть алгоритм: Дейкстри, Беллмана-Форда або A*.\n\n"
            "5. Натисніть кнопку «Знайти найкоротший шлях».\n\n"
            "6. Результат можна зберегти у файл або переглянути графічно."
        )

        label = tk.Label(
            frame,
            text=instruction_text,
            justify="left",
            anchor="nw",
            font=("Helvetica", 13),
            wraplength=640
        )
        label.grid(row=0, column=0, sticky="nsew")

        def update_wrap(event):
            label.config(wraplength=event.width - 40)

        frame.bind("<Configure>", update_wrap)

        tk.Button(
            self,
            text="Закрити",
            command=self.destroy,
            font=("Helvetica", 12),
            padx=20,
            pady=4
        ).grid(row=1, column=0, pady=10)


class TextInputWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk, directed: bool,
                 on_done: callable) -> None:
        super().__init__(master)
        self.title("Текстове введення графу")
        self.minsize(500, 400)
        self.resizable(True, True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._directed = directed
        self._on_done = on_done
        self.lift()
        self.focus_force()
        self._build()

    def _build(self) -> None:
        # Вершини
        tk.Label(self, text="Вершини (через пробіл):",
                  font=("Helvetica", 11)).grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 2))
        self._entry_vertices = tk.Entry(self, font=("Helvetica", 11))
        self._entry_vertices.grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 10))
        self._entry_vertices.focus_set()

        # Ребра
        tk.Label(self, text="Ребра (кожне на новому рядку:  звідки  куди  вага):",
                  font=("Helvetica", 11)).grid(
            row=2, column=0, sticky="w", padx=16)

        edge_frame = tk.Frame(self)
        edge_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 4))
        edge_frame.columnconfigure(0, weight=1)
        edge_frame.rowconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        sb = tk.Scrollbar(edge_frame)
        sb.grid(row=0, column=1, sticky="ns")
        self._text_edges = tk.Text(edge_frame, font=("Courier", 11),
                                    yscrollcommand=sb.set, height=8)
        self._text_edges.grid(row=0, column=0, sticky="nsew")
        sb.config(command=self._text_edges.yview)

        tk.Label(self, text="Приклад: A B 5   або   1 2 3.5",
                  font=("Helvetica", 10, "italic")).grid(
            row=4, column=0, sticky="w", padx=16)

        tk.Button(self, text="Підтвердити", command=self._confirm,
                   font=("Helvetica", 12), pady=8).grid(
            row=5, column=0, pady=14)

    def _confirm(self) -> None:
        raw_v = self._entry_vertices.get().strip()
        if not raw_v:
            messagebox.showerror("Помилка", "Введіть вершини!", parent=self)
            return
        vertices = [v.strip() for v in raw_v.replace(",", " ").split() if v.strip()]
        if len(vertices) != len(set(vertices)):
            messagebox.showerror("Помилка", "Вершини мають бути унікальними!", parent=self)
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
                messagebox.showerror("Помилка", f"Вершина '{u}' не існує.", parent=self)
                return
            if v not in g.vertices:
                messagebox.showerror("Помилка", f"Вершина '{v}' не існує.", parent=self)
                return
            try:
                w = float(ws)
            except ValueError:
                messagebox.showerror("Помилка", f"'{ws}' не є числом!", parent=self)
                return
            g.add_edge(u, v, w)
        self._on_done(g)
        self.destroy()
        messagebox.showinfo(
            "Готово",
            f"Граф задано: {len(g.vertices)} вершин, {g.edge_count()} ребер.")


if __name__ == "__main__":
    MainApp().mainloop()
