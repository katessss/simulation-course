import tkinter as tk
from tkinter import ttk
import random
import time

CELL_SIZE = 10
GRID_W = 60
GRID_H = 60
FPS = 10

# Состояния клеток
STATE_EMPTY = 0 
STATE_TREE = 1 
STATE_BURNING = 2
STATE_ASH = 3
STATE_WATER = 4

class WildfireEngine:
    def __init__(self, width, height):
        self.w = width
        self.h = height
        self.tick_count = 0
        self.rain_active = False
        self.rain_timer = 0
        
        self.grid = [[STATE_EMPTY] * self.w for _ in range(self.h)]
        self.next_grid = [[STATE_EMPTY] * self.w for _ in range(self.h)]
        self.age = [[0] * self.w for _ in range(self.h)]
        
        self.generate_world()

    def generate_world(self):
        self.tick_count = 0
        self.rain_active = False
        self.rain_timer = 0
        # генерация леса
        for y in range(self.h):
            for x in range(self.w):
                self.grid[y][x] = STATE_EMPTY
                self.age[y][x] = 0
                if random.random() < 0.62:
                    self.grid[y][x] = STATE_TREE
                    self.age[y][x] = random.randint(0, 180)
        # Генерация рек
        for cfg in [(True, 14, 2), (False, 22, 2), (True, 43, 1), (False, 48, 1)]:
            self._generate_river(*cfg)

    def _generate_river(self, is_horizontal, pos, width):
        for k in range(-width // 2, width // 2 + 1):
            for i in range(self.w if is_horizontal else self.h):
                j = random.randint(-1, 1) # извилистость
                if is_horizontal:
                    new_y = max(0, min(self.h - 1, pos + k + j))
                    self.grid[new_y][i] = STATE_WATER; self.age[new_y][i] = 0
                else:
                    new_x = max(0, min(self.w - 1, pos + k + j))
                    self.grid[i][new_x] = STATE_WATER; self.age[i][new_x] = 0

    def clear_board(self):
        # Полностью очистить поле
        for y in range(self.h):
            for x in range(self.w):
                self.grid[y][x] = STATE_EMPTY
                self.age[y][x] = 0

    def fill_forest(self):
        # Засадить всю пустую землю лесом
        for y in range(self.h):
            for x in range(self.w):
                if self.grid[y][x] == STATE_EMPTY:
                    self.grid[y][x] = STATE_TREE
                    self.age[y][x] = random.randint(0, 20) # Сажаем молодые деревья

    def trigger_rain(self):
        self.rain_active = True
        self.rain_timer = FPS * random.randint(1, 20)

    def set_cell(self, x, y, state):
        # Рука Бога
        if 0 <= x < self.w and 0 <= y < self.h:
            # Воду и огонь поджечь нельзя, остальное можно
            if state == STATE_BURNING and self.grid[y][x] == STATE_WATER and state == STATE_EMPTY:
                return
            self.grid[y][x] = state
            self.age[y][x] = 0

    def _get_neighbors(self, x, y):
        neighbors = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0: continue
                neighbors.append(self.grid[(y + dy) % self.h][(x + dx) % self.w])
        return neighbors

    def step(self, p_growth, p_lightning, humidity):
        # Один шаг симуляции
        self.tick_count += 1
        p_ash_blow = 0.05  # шасн что кучка пепла развеется по ветру за один кадр

        if self.rain_active:
            self.rain_timer -= 1
            if self.rain_timer <= 0:
                self.rain_active = False

        for y in range(self.h):
            for x in range(self.w):
                s = self.grid[y][x]

                if s == STATE_WATER:
                    self.next_grid[y][x] = STATE_WATER # с водой ничего не происходит
                    continue

                if s == STATE_BURNING: 
                    self.next_grid[y][x] = STATE_ASH # если ктелка рядом горит - то уже пепел
                    self.age[y][x] = 0
                    continue

                if s == STATE_ASH:
                    self.next_grid[y][x] = STATE_EMPTY if random.random() < p_ash_blow else STATE_ASH
                    continue

                if s == STATE_EMPTY:
                    if random.random() < p_growth:
                        self.next_grid[y][x] = STATE_TREE
                        self.age[y][x] = 0
                    else:
                        self.next_grid[y][x] = STATE_EMPTY
                    continue

                if s == STATE_TREE:
                    self.age[y][x] += 1
                    burn = False
                    
                    if random.random() < p_lightning:
                        burn = True
                    else:
                        neighbors = self._get_neighbors(x, y)
                        if STATE_BURNING in neighbors:
                            burn_chance = 0.60
                            if self.age[y][x] < 20: 
                                burn_chance -= 0.20
                            elif self.age[y][x] > 60: 
                                burn_chance += 0.20
                            
                            # Влажность дает 80% защиты от распространения огня
                            burn_chance -= humidity * 0.80
                            if self.rain_active: 
                                burn_chance -= 0.50
                            if STATE_WATER in neighbors: 
                                burn_chance -= 0.15
                            
                            if random.random() < max(burn_chance, 0.0):
                                burn = True
                                
                    if (burn and self.rain_active and random.random() < 0.80):
                        burn = False
                    self.next_grid[y][x] = STATE_BURNING if burn else STATE_TREE

        # Синхронизация миров 
        for y in range(self.h):
            for x in range(self.w):
                self.grid[y][x] = self.next_grid[y][x]

    # счетчик
    def get_stats(self):
        stats = {STATE_TREE: 0, STATE_BURNING: 0, STATE_WATER: 0, STATE_ASH: 0}
        for y in range(self.h):
            for x in range(self.w):
                s = self.grid[y][x]
                if s in stats: stats[s] += 1
        return stats

# НАСТРОЙКИ UI (Цвета)
C_BG      = "#F3F4F6"
C_PANEL   = "#FFFFFF"
C_BORDER  = "#E5E7EB"
C_GRID    = "#F9FAFB"
C_TEXT    = "#1F2937"
C_DIM     = "#6B7280"

C_TREE_Y  = "#86EFAC"
C_TREE    = "#22C55E"
C_TREE_O  = "#166534"
C_FIRE_1  = "#F87171"
C_FIRE_2  = "#FDE047"
C_FIRE_3  = "#EF4444"
C_ASH     = "#D1D5DB"
C_WATER   = "#3B82F6"
C_WATER2  = "#2563EB"

C_AMBER   = "#F59E0B"
C_CYAN    = "#0EA5E9"
C_RED     = "#EF4444"
C_GREEN   = "#10B981"

FONT_MAIN = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_NUM  = ("Consolas", 14, "bold")
FONT_MINI = ("Segoe UI", 8, "bold")

def hex_to_rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def lerp_color(c1, c2, t):
    r1,g1,b1 = hex_to_rgb(c1); r2,g2,b2 = hex_to_rgb(c2)
    return f"#{int(r1+(r2-r1)*t):02x}{int(g1+(g2-g1)*t):02x}{int(b1+(b2-b1)*t):02x}"

#  КАСТОМНЫЕ ВИДЖЕТЫ
class ModernButton(tk.Canvas):
    def __init__(self, parent, text, command, w=200, h=32, color=C_AMBER, bg_color=C_PANEL):
        super().__init__(parent, width=w, height=h, bg=bg_color, highlightthickness=0)
        self.command = command
        self.base_color = color
        self.hover_color = lerp_color(color, "#000000", 0.15)
        self.text_str = text
        self.w, self.h = w, h
        self._draw(hover=False)
        self.bind("<Button-1>", lambda _: self.command())
        self.bind("<Enter>", lambda _: self._draw(hover=True))
        self.bind("<Leave>", lambda _: self._draw(hover=False))

    def _draw(self, hover=False):
        self.delete("all")
        fill_color = self.hover_color if hover else self.base_color
        pts = [2+6,2, self.w-2-6,2, self.w-2,2, self.w-2,2+6,
               self.w-2,self.h-2-6, self.w-2,self.h-2, self.w-2-6,self.h-2, 2+6,self.h-2,
               2,self.h-2, 2,self.h-2-6, 2,2+6, 2,2]
        self.create_polygon(pts, smooth=True, fill=fill_color, outline="")
        self.create_text(self.w//2, self.h//2, text=self.text_str, fill="#FFFFFF", font=FONT_BOLD)

class TickerLabel(tk.Frame):
    def __init__(self, parent, icon, label, color):
        super().__init__(parent, bg=C_PANEL)
        inner = tk.Frame(self, bg=C_PANEL)
        inner.pack(fill=tk.X, expand=True, pady=2)
        top = tk.Frame(inner, bg=C_PANEL)
        top.pack(fill=tk.X)
        tk.Label(top, text=icon, bg=C_PANEL, fg=color, font=FONT_MAIN).pack(side=tk.LEFT)
        tk.Label(top, text=label.upper(), bg=C_PANEL, fg=C_DIM, font=FONT_MINI).pack(side=tk.LEFT, padx=4)
        self.val_lbl = tk.Label(inner, text="0", bg=C_PANEL, fg=C_TEXT, font=FONT_NUM, anchor="w")
        self.val_lbl.pack(fill=tk.X)
        bar_bg = tk.Frame(inner, bg=C_BG, height=4)
        bar_bg.pack(fill=tk.X, pady=(2,0))
        self.bar = tk.Frame(bar_bg, bg=color, height=4, width=0)
        self.bar.place(x=0, y=0, relheight=1)
        self._bar_bg = bar_bg

    def update_val(self, value, total):
        self.val_lbl.config(text=f"{value:,}")
        frac = min(value / total, 1.0) if total > 0 else 0
        w = int(self._bar_bg.winfo_width() * frac)
        self.bar.place(width=w)

class StyledScale(tk.Frame):
    def __init__(self, parent, label, vdef, color=C_AMBER):
        super().__init__(parent, bg=C_PANEL)
        header = tk.Frame(self, bg=C_PANEL)
        header.pack(fill=tk.X)
        tk.Label(header, text=label, bg=C_PANEL, fg=C_DIM, font=FONT_MINI).pack(side=tk.LEFT)
        
        self.val_lbl = tk.Label(header, text=f"{vdef:.3f}", bg=C_PANEL, fg=color, font=FONT_MINI)
        self.val_lbl.pack(side=tk.RIGHT)
        self.var = tk.DoubleVar(value=vdef)
        self.var.trace_add("write", lambda *_: self.val_lbl.config(text=f"{self.var.get():.3f}"))
        
        style = ttk.Style()
        style.configure(f"{id(self)}.Horizontal.TScale", background=C_PANEL, troughcolor=C_BG)
        s = ttk.Scale(self, from_=0.0, to=1.0, variable=self.var, orient=tk.HORIZONTAL, style=f"{id(self)}.Horizontal.TScale")
        s.pack(fill=tk.X, pady=(2, 6))

# УПРАВЛЕНИЕ И ИНТЕРФЕЙС
class WildfireApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Симулятор лесного пожара")
        self.root.configure(bg=C_BG)
        
        W = GRID_W * CELL_SIZE + 280
        H = GRID_H * CELL_SIZE + 120
        self.root.geometry(f"{W}x{H}")
        self.root.resizable(False, False)

        self.engine = WildfireEngine(GRID_W, GRID_H)
        self.running = False
        self._loop_id = None
        self.elapsed_time = 0.0
        self.last_time = None

        self._build_ui()
        self._init_canvas()
        self.update_graphics()
        self._clock_tick()

    def _build_ui(self):
        header = tk.Frame(self.root, bg=C_BG, height=50)
        header.pack(fill=tk.X, padx=20, pady=(15, 0))
        header.pack_propagate(False)

        tk.Label(header, text="◈", bg=C_BG, fg=C_AMBER, font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)
        tk.Label(header, text="СИМУЛЯТОР", bg=C_BG, fg=C_TEXT, font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT, padx=(4,0))
        tk.Label(header, text="ЛЕСНОГО ПОЖАРА", bg=C_BG, fg=C_DIM, font=FONT_MAIN).pack(side=tk.LEFT, pady=6, padx=8)

        self.clock_lbl = tk.Label(header, text="00:00 • ТАКТ 0", bg=C_BG, fg=C_DIM, font=FONT_BOLD)
        self.clock_lbl.pack(side=tk.RIGHT, pady=8)

        self.status_dot = tk.Label(header, text="●", bg=C_BG, fg=C_DIM, font=("Segoe UI", 12))
        self.status_dot.pack(side=tk.RIGHT, padx=4, pady=6)

        tk.Frame(self.root, bg=C_BORDER, height=1).pack(fill=tk.X, padx=20)

        body = tk.Frame(self.root, bg=C_BG)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # Сетка (Канвас)
        canvas_wrap = tk.Frame(body, bg=C_BORDER, padx=1, pady=1)
        canvas_wrap.pack(side=tk.LEFT)

        self.canvas = tk.Canvas(canvas_wrap, width=GRID_W * CELL_SIZE, height=GRID_H * CELL_SIZE, bg=C_GRID, highlightthickness=0, cursor="crosshair")
        self.canvas.pack()
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<Button-1>",  self._on_mouse_drag)

        # Боковая панель
        panel_wrap = tk.Frame(body, bg=C_BORDER, padx=1, pady=1)
        panel_wrap.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))
        
        panel = tk.Frame(panel_wrap, bg=C_PANEL, width=260)
        panel.pack(fill=tk.BOTH, expand=True)
        panel.pack_propagate(False)

        inner = tk.Frame(panel, bg=C_PANEL, padx=16)
        inner.pack(fill=tk.BOTH, expand=True, pady=10)

        # --- КИСТИ (ИНСТРУМЕНТЫ РИСОВАНИЯ) ---
        self._section_title(inner, "ИНСТРУМЕНТЫ (КИСТЬ)")
        self.draw_var = tk.StringVar(value="none")
        
        tools = [
            ("none",       "Курсор",   C_DIM),
            ("extinguish", "Ластик",   "#9CA3AF"),
            ("tree",       "Лес",      C_TREE),
            ("water",      "Вода",     C_CYAN),
            ("fire",       "Огонь",    C_RED),
        ]
        
        tool_frame = tk.Frame(inner, bg=C_PANEL)
        tool_frame.pack(fill=tk.X, pady=(2, 6))
        
        # 5 инструментов. Последний (Огонь) растягивается на 2 колонки
        for i, (val, lbl, col) in enumerate(tools):
            btn = tk.Radiobutton(
                tool_frame, text=lbl, variable=self.draw_var, value=val,
                bg=C_BG, fg=C_TEXT, selectcolor=C_BORDER,
                activebackground=C_BG, activeforeground=col,
                font=FONT_MAIN, indicatoron=False, relief="flat", bd=0, padx=5, pady=2
            )
            if i == 4: # Инструмент "Огонь"
                btn.grid(row=i//2, column=0, columnspan=2, sticky="ew", padx=2, pady=2)
            else:
                btn.grid(row=i//2, column=i%2, sticky="ew", padx=2, pady=2)
            
        tool_frame.grid_columnconfigure(0, weight=1)
        tool_frame.grid_columnconfigure(1, weight=1)

        tk.Frame(inner, bg=C_BG, height=2).pack(fill=tk.X, pady=4)

        # --- ПАРАМЕТРЫ ПРИРОДЫ (ОТ 0.0 ДО 1.0) ---
        self._section_title(inner, "ВЕРОЯТНОСТИ И ФИЗИКА (0 - 1)")
        self.sv_growth   = StyledScale(inner, "РОСТ ДЕРЕВЬЕВ", 0.05, color=C_GREEN)
        self.sv_fire     = StyledScale(inner, "ШАНС МОЛНИИ", 0.01, color=C_AMBER)
        self.sv_humidity = StyledScale(inner, "ВЛАЖНОСТЬ", 0.30, color=C_CYAN)
        for s in (self.sv_growth, self.sv_fire, self.sv_humidity): s.pack(fill=tk.X)

        tk.Frame(inner, bg=C_BG, height=2).pack(fill=tk.X, pady=4)

        # --- ГЛОБАЛЬНЫЕ КНОПКИ УПРАВЛЕНИЯ ---
        self._section_title(inner, "ГЛОБАЛЬНЫЕ ДЕЙСТВИЯ")
        bf = tk.Frame(inner, bg=C_PANEL)
        bf.pack(fill=tk.X, pady=(2,0))
        
        row1 = tk.Frame(bf, bg=C_PANEL)
        row1.pack(fill=tk.X, pady=2)
        ModernButton(row1, "▶ СТАРТ / ПАУЗА", self.toggle_sim, w=224, color=C_TEXT).pack()

        row2 = tk.Frame(bf, bg=C_PANEL)
        row2.pack(fill=tk.X, pady=2)
        ModernButton(row2, "🌲 ВЕСЬ ЛЕС", self.fill_board_forest, w=110, color=C_TREE).pack(side=tk.LEFT)
        ModernButton(row2, "✖ ЧИТСКА", self.clear_board_empty, w=80, color="#9CA3AF").pack(side=tk.RIGHT)

        row3 = tk.Frame(bf, bg=C_PANEL)
        row3.pack(fill=tk.X, pady=2)
        ModernButton(row3, "⛈ ДОЖДЬ", lambda: self.engine.trigger_rain(), w=110, color=C_CYAN).pack(side=tk.LEFT)
        ModernButton(row3, "↺ СБРОС", self.reset_sim, w=80, color=C_DIM).pack(side=tk.RIGHT)

        # --- СТАТИСТИКА ---
        tk.Frame(inner, bg=C_BG, height=2).pack(fill=tk.X, pady=8)
        self._section_title(inner, "СТАТИСТИКА")
        stats_grid = tk.Frame(inner, bg=C_PANEL)
        stats_grid.pack(fill=tk.X)
        self.stat_trees = TickerLabel(stats_grid, "🌲", "Деревья", C_GREEN)
        self.stat_fire  = TickerLabel(stats_grid, "🔥", "Огонь", C_RED)
        for w in (self.stat_trees, self.stat_fire): w.pack(fill=tk.X)

        self.rain_lbl = tk.Label(panel, text="", bg=C_PANEL, fg=C_CYAN, font=FONT_BOLD)
        self.rain_lbl.pack(side=tk.BOTTOM, pady=8)

    def _section_title(self, parent, title):
        tk.Label(parent, text=title, bg=C_PANEL, fg=C_DIM, font=FONT_MINI).pack(anchor="w", pady=(0, 2))

    def _init_canvas(self):
        self.rects = []
        for y in range(GRID_H):
            row = []
            for x in range(GRID_W):
                x0, y0 = x*CELL_SIZE, y*CELL_SIZE
                r = self.canvas.create_rectangle(x0, y0, x0+CELL_SIZE, y0+CELL_SIZE, fill=C_GRID, outline="")
                row.append(r)
            self.rects.append(row)

    def _get_ui_color(self, state, x, y):
        if state == STATE_BURNING: return random.choice([C_FIRE_3, C_FIRE_1, C_FIRE_2, C_FIRE_1, C_FIRE_3])
        if state == STATE_TREE:
            a = self.engine.age[y][x]
            if a < 20: return C_TREE_Y
            if a < 60: return C_TREE
            return C_TREE_O
        if state == STATE_WATER: return C_WATER if random.random() > 0.04 else C_WATER2
        return {STATE_EMPTY: C_GRID, STATE_ASH: C_ASH}.get(state, C_GRID)

    def update_graphics(self):
        for y in range(GRID_H):
            for x in range(GRID_W):
                state = self.engine.grid[y][x]
                color = self._get_ui_color(state, x, y)
                self.canvas.itemconfig(self.rects[y][x], fill=color)

        stats = self.engine.get_stats()
        total = GRID_W * GRID_H
        self.stat_trees.update_val(stats[STATE_TREE], total)
        self.stat_fire.update_val(stats[STATE_BURNING], total)

        if self.engine.rain_active:
            sec = int(self.engine.rain_timer / FPS)
            self.rain_lbl.config(text=f"⛈ ДОЖДЬ ИДЕТ: {sec} сек")
        else:
            self.rain_lbl.config(text="")

    def _clock_tick(self):
        if self.running:
            current = time.time()
            if self.last_time: self.elapsed_time += (current - self.last_time)
            self.last_time = current

            m, s = divmod(int(self.elapsed_time), 60)
            self.clock_lbl.config(text=f"{m:02d}:{s:02d} • ТАКТ {self.engine.tick_count}")
            self.status_dot.config(fg=C_GREEN if (self.engine.tick_count % 2 == 0) else C_TEXT)
        else:
            self.status_dot.config(fg=C_DIM)
            self.last_time = None 
        self.root.after(500, self._clock_tick)

    def _on_mouse_drag(self, ev):
        mode = self.draw_var.get()
        if mode == "none": return
        x, y = ev.x // CELL_SIZE, ev.y // CELL_SIZE
        state_map = {"water": STATE_WATER, "fire": STATE_BURNING, "extinguish": STATE_EMPTY, "tree": STATE_TREE}
        
        if mode in state_map:
            self.engine.set_cell(x, y, state_map[mode])
            if 0 <= x < GRID_W and 0 <= y < GRID_H:
                self.canvas.itemconfig(self.rects[y][x], fill=self._get_ui_color(self.engine.grid[y][x], x, y))

    def fill_board_forest(self):
        """Заполняет всё поле лесом по кнопке"""
        self.engine.fill_forest()
        self.update_graphics()
        
    def clear_board_empty(self):
        """Очищает всё поле по кнопке"""
        self.engine.clear_board()
        self.update_graphics()

    def loop(self):
        if self.running:
            # СЧИТЫВАЕМ ЗНАЧЕНИЯ ПРЯМО С ПОЛЗУНКОВ
            g = self.sv_growth.var.get()
            l = self.sv_fire.var.get()
            h = self.sv_humidity.var.get()
            self.engine.step(g, l, h)
            # ПЕРЕРИСОВЫВАЕМ 
            self.update_graphics()
            # СЛЕДУЮЩИЙ ТАКТ
            self._loop_id = self.root.after(int(1000/FPS), self.loop)

    def toggle_sim(self):
        self.running = not self.running
        if self.running:
            self.last_time = time.time() 
            self.loop()
        else:
            if self._loop_id: self.root.after_cancel(self._loop_id); self._loop_id = None

    def reset_sim(self):
        self.running = False
        if self._loop_id: self.root.after_cancel(self._loop_id); self._loop_id = None
        self.elapsed_time = 0.0; self.last_time = None
        self.engine.generate_world()
        self.clock_lbl.config(text="00:00 • ТАКТ 0")
        self.update_graphics()

if __name__ == "__main__":
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    app = WildfireApp(root)
    root.mainloop()