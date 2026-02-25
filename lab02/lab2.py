import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from numba import jit

@jit(nopython=True)
def calculate_heat(Tl, Tr, L, h, total_time, dt, rho, c, lmd):
    Nx = int(L / h)
    Nt = int(total_time / dt)

    T = np.zeros(Nx + 1) 
    T[0], T[-1] = Tl, Tr

    A = lmd / h**2 # Коэффициент влияния левого соседа
    C = A # Коэффициент влияния правого соседа 
    B = 2 * lmd / h**2 + rho * c / dt # Коэффициент самой точки 

    alpha = np.zeros(Nx + 1) 
    beta = np.zeros(Nx + 1)

    for _ in range(Nt):
        alpha[0] = 0.0
        beta[0] = Tl
        # Прямой ход прогонки
        for i in range(1, Nx):
            Fi = -(rho * c / dt) * T[i]
            denom = B - C * alpha[i - 1]
            alpha[i] = A / denom
            beta[i] = (C * beta[i - 1] - Fi) / denom 

        # Обратный ход
        T_new = np.zeros(Nx + 1)
        T_new[-1] = Tr
        T_new[0] = Tl
        for i in range(Nx - 1, 0, -1):
            T_new[i] = alpha[i] * T_new[i + 1] + beta[i] 
        
        T = T_new 

    x_axis = np.linspace(0, L, Nx + 1)
    return x_axis, T, T[Nx // 2]

class HeatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Имитационное моделирование теплопроводности")
        self.root.geometry("1200x800")

        # Панель управления
        side_panel = ttk.Frame(root, padding=10)
        side_panel.pack(side=tk.LEFT, fill=tk.Y)

        # Функция для создания полей ввода
        self.entries = {}
        def create_entry(label, default, key):
            ttk.Label(side_panel, text=label).pack(anchor="w")
            entry = ttk.Entry(side_panel)
            entry.insert(0, default)
            entry.pack(fill="x", pady=2)
            self.entries[key] = entry

        create_entry("Длина пластины L (м):", "0.4", "L")
        create_entry("Темп. слева (°C):", "0", "Tl")
        create_entry("Темп. справа (°C):", "200", "Tr")
        
        ttk.Separator(side_panel, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(side_panel, text="Свойства материала:", font=('Helvetica', 10, 'bold')).pack(anchor="w")
        
        create_entry("Плотность rho (кг/м³):", "7800", "rho")
        create_entry("Теплоемкость c (Дж/кг·К):", "460", "c")
        create_entry("Теплопроводность lmd (Вт/м·К):", "46", "lmd")

        self.btn_task = ttk.Button(side_panel, text="Выполнить задание", command=self.run_experiment)
        self.btn_task.pack(pady=15, fill="x")

        self.btn_clear = ttk.Button(side_panel, text="Очистить результаты", command=self.clear)
        self.btn_clear.pack(fill="x")

        # Таблица результатов
        self.tree = ttk.Treeview(side_panel, columns=("dt", "h", "temp"), show='headings', height=10)
        self.tree.heading("dt", text="dt (с)")
        self.tree.heading("h", text="h (м)")
        self.tree.heading("temp", text="T в центре")
        self.tree.column("dt", width=70); self.tree.column("h", width=70); self.tree.column("temp", width=90)
        self.tree.pack(pady=10)

        self.fig = Figure(figsize=(7, 6))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Распределение температуры")
        self.ax.set_xlabel("Координата x (м)")
        self.ax.set_ylabel("Температура T (°C)")
        self.ax.grid(True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    def run_experiment(self):
        try:
            # Считываем параметры из полей ввода
            L = float(self.entries["L"].get())
            Tl = float(self.entries["Tl"].get())
            Tr = float(self.entries["Tr"].get())
            rho = float(self.entries["rho"].get())
            c = float(self.entries["c"].get())
            lmd = float(self.entries["lmd"].get())
            
            dts = [0.1, 0.01, 0.001, 0.0001]
            hs = [0.1, 0.01, 0.001, 0.0001]
            
            for dt in dts:
                for h in hs:
                    # Запускаем расчет 
                    x, T, T_center = calculate_heat(Tl, Tr, L, h, 2.0, dt, rho, c, lmd)
                    
                    self.tree.insert('', tk.END, values=(dt, h, f"{T_center:.8f}"))
                    
                    # Визуализируем только сетки h >= 0.01, чтобы график не "засорялся"
                    if h >= 0.01:
                        self.ax.plot(x, T, label=f"dt={dt} h={h}")
            
            self.ax.legend(fontsize='small', ncol=2, loc='upper left')
            self.canvas.draw()
            
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите корректные числовые значения параметров.")

    def clear(self):
        self.ax.clear()
        self.ax.set_title("Распределение температуры")
        self.ax.grid(True)
        self.canvas.draw()
        for i in self.tree.get_children():
            self.tree.delete(i)

if __name__ == "__main__":
    root = tk.Tk()
    app = HeatApp(root)
    root.mainloop()