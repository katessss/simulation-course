import tkinter as tk
from tkinter import ttk, messagebox
import random
import math


C = {
    "bg":      "#18181B",   # фон окна
    "surface": "#27272A",   # карточки / поля
    "border":  "#3F3F46",   # рамки
    "accent":  "#6EE7B7",   # мятный акцент
    "accent2": "#F472B6",   # розовый акцент (8-ball)
    "text":    "#FAFAFA",
    "muted":   "#A1A1AA",
    "ok":      "#6EE7B7",
    "err":     "#F87171",
    "tab_bg":  "#1F1F22",
}

FT = ("Segoe UI",  9)
FB = ("Segoe UI", 11)
FM = ("Consolas",  10)
FBIG = ("Segoe UI", 48, "bold")
FMED = ("Segoe UI", 20, "bold")
FBTN = ("Segoe UI", 10, "bold")


#  АЛГОРИТМ МОИСЕЕВА
def moiseyev_generate(answers: list[tuple[str, float]]) -> str:
    A = random.random()
    for name, p_k in answers:
        A -= p_k
        if A <= 0:
            return name
    return answers[-1][0]


class App:
    """
    Структура:
        App.__init__ - создаёт окно, стиль, notebook, вызывает build-методы
        App._build_tab_custom  - вкладка «Свои события»
        App._build_tab_ball  - вкладка «Magic 8-Ball»
        App._add_row / _del_row - управление строками таблицы
        App._update_sum - пересчёт индикатора суммы
        App._run_custom  - генерация события (вкладка 1)
        App._spin / _fade_in / _show_prediction - анимация шара
    """

    #  Инициализация
      
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Симулятор случайных событий")
        self.root.geometry("640x560")
        self.root.configure(bg=C["bg"])
        self.root.resizable(False, False)
 
        self._apply_style()
 
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(expand=True, fill="both")
 
        # вкладка 1 — свои события
        self.event_rows: list[tuple[tk.Entry, tk.Entry, tk.Frame]] = []
        self._build_tab_custom()
 
        # вкладка 2 — magic 8-ball
        self.spinning     = False
        self.ball_angle   = 0.0
        self.hex_coords: list[float] = []
        self._build_tab_ball()
 
      
    #  Стиль ttk
      
    def _apply_style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TNotebook",
                    background=C["bg"], borderwidth=0, tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab",
                    background=C["tab_bg"], foreground=C["muted"],
                    font=("Segoe UI", 9, "bold"), padding=[20, 9], borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", C["surface"])],
              foreground=[("selected", C["accent"])])
 
      
    #  Вспомогательные виджеты
      
    def _label(self, parent, text, font=None, color=None, **kw) -> tk.Label:
        return tk.Label(parent, text=text,
                        font=font or FB, fg=color or C["text"],
                        bg=parent["bg"], **kw)
 
    def _entry(self, parent, width=14) -> tk.Entry:
        return tk.Entry(parent, width=width, font=FM,
                        bg=C["surface"], fg=C["text"],
                        insertbackground=C["text"],
                        highlightthickness=1,
                        highlightbackground=C["border"],
                        highlightcolor=C["accent"],
                        relief="flat")
 
    def _btn(self, parent, text, cmd, accent=False) -> tk.Button:
        bg  = C["accent"] if accent else C["surface"]
        fg  = C["bg"]     if accent else C["muted"]
        hbg = C["muted"]  if accent else C["border"]
        b = tk.Button(parent, text=text, command=cmd,
                      font=FBTN, bg=bg, fg=fg,
                      activebackground=hbg, activeforeground=C["text"],
                      relief="flat", cursor="hand2",
                      padx=16, pady=7, bd=0)
        b.bind("<Enter>", lambda _: b.config(bg=hbg))
        b.bind("<Leave>", lambda _: b.config(bg=bg))
        return b
 
    def _divider(self, parent):
        tk.Frame(parent, height=1, bg=C["border"]).pack(fill="x", padx=18, pady=5)
 
      
    #  ВКЛАДКА 1 — СВОИ СОБЫТИЯ
      
    def _build_tab_custom(self):
        f = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(f, text="  Свои события  ")
 
        # заголовочная полоса
        hdr = tk.Frame(f, bg=C["surface"],
                       highlightthickness=1, highlightbackground=C["border"])
        hdr.pack(fill="x", padx=20, pady=(18, 6))
 
        self._label(hdr, "Алгоритм Моисеева",
                    font=("Segoe UI", 12, "bold"), color=C["accent"]).pack(
                    side="left", padx=16, pady=10)
        self._label(hdr, "A := ξ − p₁ − p₂ − …   первое A ≤ 0",
                    font=FM, color=C["muted"]).pack(side="right", padx=16)
 
        # таблица
        tbl = tk.Frame(f, bg=C["surface"],
                       highlightthickness=1, highlightbackground=C["border"])
        tbl.pack(fill="x", padx=20)
 
        # шапка таблицы
        col_hdr = tk.Frame(tbl, bg=C["border"])
        col_hdr.pack(fill="x")
        for txt, w in [("#", 3), ("Событие", 16), ("Вероятность", 12), ("Доля", 10)]:
            tk.Label(col_hdr, text=txt, font=FT, fg=C["muted"],
                     bg=C["border"], width=w, anchor="w").pack(
                     side="left", padx=(10, 0), pady=5)
 
        self._tbl_body = tk.Frame(tbl, bg=C["surface"])
        self._tbl_body.pack(fill="x")
 
        # сумма + кнопки
        ctrl = tk.Frame(tbl, bg=C["surface"])
        ctrl.pack(fill="x", padx=10, pady=8)
 
        self._btn(ctrl, "+ строка", self._add_row).pack(side="left", padx=(0, 4))
        self._btn(ctrl, "− строка", self._del_row).pack(side="left")
 
        self._sum_lbl = tk.Label(ctrl, text="", font=FT,
                                 fg=C["ok"], bg=C["surface"])
        self._sum_lbl.pack(side="right", padx=8)
 
        # результат + кнопка генерации
        res_row = tk.Frame(f, bg=C["bg"])
        res_row.pack(fill="x", padx=20, pady=10)
 
        self._custom_res = tk.Label(res_row, text="—", font=FMED,
                                    fg=C["muted"], bg=C["bg"])
        self._custom_res.pack(side="left")
 
        self._btn(res_row, "СГЕНЕРИРОВАТЬ",
                  self._run_custom, accent=True).pack(side="right")
 
        # начальные строки
        for n, p in [("Победа", "0.40"), ("Ничья", "0.35"), ("Поражение", "0.25")]:
            self._add_row(n, p)
 
      
    #  Управление строками таблицы
      
    def _add_row(self, name: str = "", prob: str = ""):
        idx = len(self.event_rows)
        row_f = tk.Frame(self._tbl_body, bg=C["surface"])
        row_f.pack(fill="x")
 
        tk.Label(row_f, text=f"{idx+1}", width=3, font=FM,
                 fg=C["accent"], bg=C["surface"], anchor="center").pack(
                 side="left", padx=(10, 4), pady=4)
 
        ne = self._entry(row_f, width=16)
        ne.insert(0, name)
        ne.pack(side="left", padx=(0, 8), ipady=3)
 
        pe = self._entry(row_f, width=10)
        pe.insert(0, prob)
        pe.pack(side="left", ipady=3)
 
        # мини-бар
        bar_bg   = tk.Frame(row_f, bg=C["border"], height=4, width=80)
        bar_bg.pack(side="left", padx=(10, 0))
        bar_fill = tk.Frame(bar_bg, bg=C["accent"], height=4, width=0)
        bar_fill.place(x=0, y=0, height=4)
 
        def refresh(*_):
            try:
                w = int(min(max(float(pe.get()), 0), 1) * 80)
            except ValueError:
                w = 0
            bar_fill.place(x=0, y=0, height=4, width=w)
            self._update_sum()
 
        pe.bind("<KeyRelease>", refresh)
        self.event_rows.append((ne, pe, row_f))
        self._update_sum()
        refresh()
 
    def _del_row(self):
        if len(self.event_rows) > 1:
            *_, row_f = self.event_rows.pop()
            row_f.destroy()
            self._update_sum()
 
    def _update_sum(self):
        total = 0.0
        for _, pe, _ in self.event_rows:
            try:
                total += float(pe.get())
            except ValueError:
                pass
        ok = abs(total - 1.0) < 0.001
        self._sum_lbl.config(
            text=f"{'✓' if ok else '✗'}  сумма = {total:.4f}",
            fg=C["ok"] if ok else C["err"]
        )
 
      
    #  Генерация (вкладка 1)
      
    def _run_custom(self):
        answers = []
        for ne, pe, _ in self.event_rows:
            name = ne.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Название события не может быть пустым")
                return
            try:
                p = float(pe.get())
            except ValueError:
                messagebox.showerror("Ошибка", f"Некорректная вероятность для «{name}»")
                return
            if p < 0:
                messagebox.showerror("Ошибка", f"Вероятность «{name}» < 0")
                return
            answers.append((name, p))
 
        total = sum(p for _, p in answers)
        if abs(total - 1.0) > 0.001:
            messagebox.showerror("Ошибка",
                                 f"Сумма = {total:.4f}, должна быть 1.0")
            return
 
        result = moiseyev_generate(answers)
        self._custom_res.config(text=result, fg=C["accent"])
 
      
    #  ВКЛАДКА 2 — MAGIC 8-BALL
      
    _MAGIC_DEFAULTS = [
        ("Да",             "0.125"),
        ("Нет",            "0.125"),
        ("Скорее всего",   "0.125"),
        ("Сомнительно",    "0.125"),
        ("Без сомнений",   "0.125"),
        ("Спроси позже",   "0.125"),
        ("Определённо да", "0.125"),
        ("Маловероятно",   "0.125"),
    ]
 
    def _build_tab_ball(self):
        f = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(f, text="  Magic 8-Ball  ")
 
        # ── левая колонка: шар ──
        panes = tk.Frame(f, bg=C["bg"])
        panes.pack(fill="both", expand=True, padx=12, pady=(12, 8))
 
        left = tk.Frame(panes, bg=C["bg"])
        left.pack(side="left", fill="y")
 
        self._label(left, "Magic 8-Ball",
                    font=("Segoe UI", 12, "bold"),
                    color=C["accent2"]).pack(pady=(4, 2))
        self._label(left, "нажмите на шар",
                    font=FT, color=C["muted"]).pack()
 
        self._cv = tk.Canvas(left, width=300, height=300,
                             bg=C["bg"], highlightthickness=0)
        self._cv.pack(pady=(4, 0))
        self._draw_ball()
 
        # ── правая колонка: таблица ответов ──
        right = tk.Frame(panes, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True, padx=(14, 0))
 
        # заголовок
        hdr = tk.Frame(right, bg=C["surface"],
                       highlightthickness=1, highlightbackground=C["border"])
        hdr.pack(fill="x", pady=(22, 0))
        self._label(hdr, "Ответы шара",
                    font=("Segoe UI", 10, "bold"),
                    color=C["accent2"]).pack(side="left", padx=12, pady=7)
 
        # шапка колонок
        col_hdr = tk.Frame(right, bg=C["border"])
        col_hdr.pack(fill="x")
        for txt, w in [("#", 2), ("Ответ", 12), ("Вер-ть", 7)]:
            tk.Label(col_hdr, text=txt, font=FT, fg=C["muted"],
                     bg=C["border"], width=w, anchor="w").pack(
                     side="left", padx=(8, 0), pady=4)
 
        # тело таблицы
        self._ball_tbl = tk.Frame(right, bg=C["surface"],
                                  highlightthickness=1,
                                  highlightbackground=C["border"])
        self._ball_tbl.pack(fill="x")
 
        self.ball_rows: list[tuple[tk.Entry, tk.Entry, tk.Frame]] = []
 
        # кнопки + сумма
        bctrl = tk.Frame(right, bg=C["bg"])
        bctrl.pack(fill="x", pady=(5, 0))
        self._btn(bctrl, "+ строка", self._ball_add_row).pack(side="left", padx=(0, 4))
        self._btn(bctrl, "− строка", self._ball_del_row).pack(side="left")
 
        self._ball_sum_lbl = tk.Label(bctrl, text="", font=FT,
                                      fg=C["ok"], bg=C["bg"])
        self._ball_sum_lbl.pack(side="right")
 
        # начальные строки
        for name, prob in self._MAGIC_DEFAULTS:
            self._ball_add_row(name, prob)
 
      
    #  Управление строками таблицы шара
      
    def _ball_add_row(self, name: str = "", prob: str = ""):
        idx   = len(self.ball_rows)
        row_f = tk.Frame(self._ball_tbl, bg=C["surface"])
        row_f.pack(fill="x")
 
        tk.Label(row_f, text=f"{idx+1}", width=2, font=FM,
                 fg=C["accent2"], bg=C["surface"], anchor="center").pack(
                 side="left", padx=(8, 3), pady=3)
 
        ne = self._entry(row_f, width=12)
        ne.insert(0, name)
        ne.pack(side="left", padx=(0, 6), ipady=2)
 
        pe = self._entry(row_f, width=6)
        pe.insert(0, prob)
        pe.pack(side="left", ipady=2)
 
        pe.bind("<KeyRelease>", lambda *_: self._ball_update_sum())
        self.ball_rows.append((ne, pe, row_f))
        self._ball_update_sum()
 
    def _ball_del_row(self):
        if len(self.ball_rows) > 1:
            *_, row_f = self.ball_rows.pop()
            row_f.destroy()
            self._ball_update_sum()
 
    def _ball_update_sum(self):
        total = 0.0
        for _, pe, _ in self.ball_rows:
            try:
                total += float(pe.get())
            except ValueError:
                pass
        ok = abs(total - 1.0) < 0.001
        self._ball_sum_lbl.config(
            text=f"{'✓' if ok else '✗'}  {total:.4f}",
            fg=C["ok"] if ok else C["err"]
        )
 
    def _get_ball_answers(self) -> list[tuple[str, float]] | None:
        """Считывает строки таблицы шара. Возвращает None при ошибке."""
        answers = []
        for ne, pe, _ in self.ball_rows:
            name = ne.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Название ответа не может быть пустым")
                return None
            try:
                p = float(pe.get())
            except ValueError:
                messagebox.showerror("Ошибка", f"Некорректная вероятность для «{name}»")
                return None
            if p < 0:
                messagebox.showerror("Ошибка", f"Вероятность «{name}» < 0")
                return None
            answers.append((name, p))
 
        total = sum(p for _, p in answers)
        if abs(total - 1.0) > 0.001:
            messagebox.showerror("Ошибка",
                                 f"Сумма вероятностей = {total:.4f}\nДолжна быть 1.0")
            return None
        return answers
 
    def _draw_ball(self):
        cv = self._cv
        cx = cy = 148
        R  = 118
 
        # ── размытая тень ──
        for i in range(20, 0, -1):
            a   = int(14 * i / 20)
            col = f"#{a:02x}{a:02x}{a:02x}"
            cv.create_oval(cx - R + 12 + (20 - i),
                           cy - R + 18 + (20 - i) * 0.6,
                           cx + R + 12 + (20 - i),
                           cy + R + 18 + (20 - i) * 0.6,
                           fill=col, outline="")
 
        # ── тело шара: глубокий фиолетово-чёрный ──
        for i in range(140):
            t  = i / 140
            rv = int(18 + t * 22)          # тёмно-фиолетовый к краям светлее
            gv = int(6  + t * 8)
            bv = int(38 + t * 30)
            cv.create_oval(cx - R + i * 0.82, cy - R + i * 0.82,
                           cx + R - i * 0.82, cy + R - i * 0.82,
                           fill=f"#{rv:02x}{gv:02x}{bv:02x}", outline="")
 
        # ── внутреннее свечение (мистический туман) ──
        ir  = 54
        icy = cy + 6
        for i in range(30, 0, -1):
            t  = (i / 30) ** 1.4
            rv = int(90  * t)
            gv = int(20  * t)
            bv = int(160 * t)
            rad = int(ir * i / 30)
            cv.create_oval(cx - rad, icy - rad, cx + rad, icy + rad,
                           fill=f"#{rv:02x}{gv:02x}{bv:02x}", outline="")
 
        # ── кольцо вокруг внутреннего круга ──
        cv.create_oval(cx - ir - 3, icy - ir - 3,
                       cx + ir + 3, icy + ir + 3,
                       outline="#7B2FBE", width=1)
        cv.create_oval(cx - ir, icy - ir,
                       cx + ir, icy + ir,
                       outline="#C084FC", width=1)
 
        # ── тонкая обводка шара ──
        cv.create_oval(cx - R, cy - R, cx + R, cy + R,
                       outline="#3B0764", width=2)
 
        # ── блик верхний левый ──
        for i in range(20, 0, -1):
            t   = (i / 20) ** 1.8
            rv  = int(180 * t)
            gv  = int(140 * t)
            bv  = int(255 * t)
            bx, by = cx - 36, cy - 52
            hw = int(32 * i / 20)
            hh = int(18 * i / 20)
            cv.create_oval(bx - hw, by - hh, bx + hw, by + hh,
                           fill=f"#{rv:02x}{gv:02x}{bv:02x}", outline="")
        # маленький яркий зайчик
        for i in range(8, 0, -1):
            t   = (i / 8) ** 1.1
            val = int(255 * t)
            bx, by = cx - 42, cy - 58
            hw = int(10 * i / 8)
            hh = int(6  * i / 8)
            cv.create_oval(bx - hw, by - hh, bx + hw, by + hh,
                           fill=f"#{val:02x}{val:02x}{val:02x}", outline="")
 
        # ── маленький блик снизу-справа (рефлекс) ──
        for i in range(10, 0, -1):
            t   = (i / 10) ** 2
            rv  = int(80  * t)
            gv  = int(30  * t)
            bv  = int(120 * t)
            bx, by = cx + 52, cy + 60
            hw = int(18 * i / 10)
            hh = int(10 * i / 10)
            cv.create_oval(bx - hw, by - hh, bx + hw, by + hh,
                           fill=f"#{rv:02x}{gv:02x}{bv:02x}", outline="")
 
        # ── шестиугольник для анимации вращения ──
        self.hex_coords = []
        self._ball_cx   = cx
        self._ball_icy  = icy
        for i in range(6):
            a = math.radians(60 * i - 30)
            self.hex_coords.extend([
                cx  + ir * 0.82 * math.cos(a),
                icy + ir * 0.82 * math.sin(a),
            ])
        self._hex = cv.create_polygon(self.hex_coords,
                                      fill="#1A0533", outline="#7B2FBE",
                                      width=0.5)
 
        # ── текст ответа ──
        self._ball_text = cv.create_text(cx, icy,
                                         text="?",
                                         fill="#7B4FA0",
                                         font=("Georgia", 13, "bold"),
                                         justify="center")
 
        cv.bind("<Button-1>", self._on_click)
        cv.config(cursor="hand2")
 
      
    #  Анимация шара
      
    def _on_click(self, _event=None):
        if self.spinning:
            return
        answers = self._get_ball_answers()
        if answers is None:
            return
        self.spinning = True
        self._pending_answer = moiseyev_generate(answers)
        self._spin()
 
    def _spin(self, step: int = 0, total: int = 55):
        if step < total:
            self.ball_angle += (2 * math.pi) / total
            self._rotate_hex(self.ball_angle)
            self._cv.itemconfig(self._ball_text, text="")
            self.root.after(16, self._spin, step + 1, total)
        else:
            self.ball_angle = 0
            self._rotate_hex(0)
            self.spinning = False
            self._fade_in(self._pending_answer)
 
    def _rotate_hex(self, angle: float):
        cx  = self._ball_cx
        cy  = self._ball_icy
        coords = []
        for i in range(0, len(self.hex_coords), 2):
            dx = self.hex_coords[i]     - cx
            dy = self.hex_coords[i + 1] - cy
            coords += [
                cx + dx * math.cos(angle) - dy * math.sin(angle),
                cy + dx * math.sin(angle) + dy * math.cos(angle),
            ]
        self._cv.coords(self._hex, coords)
        self._cv.coords(self._ball_text, cx, cy)
 
    def _fade_in(self, text: str, step: int = 0, total: int = 18):
        if step <= total:
            t  = step / total
            rv = min(int((180 + 75 * t) * t), 255)
            gv = min(int(120 * t * t), 255)
            bv = min(int(255 * t), 255)
            self._cv.itemconfig(self._ball_text,
                                text=text,
                                fill=f"#{rv:02x}{gv:02x}{bv:02x}",
                                font=("Georgia", 13, "bold"))
            self.root.after(28, self._fade_in, text, step + 1, total)
 
      
    #  Запуск
      
    def run(self):
        self.root.mainloop()
 
 
#  ТОЧКА ВХОДА
if __name__ == "__main__":
    App().run()