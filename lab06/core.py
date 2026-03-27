import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy import stats

class LabWorkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №6: Моделирование СВ")
        self.root.geometry("1200x950")

        self.style = ttk.Style()
        self.style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both')

        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="ЛР 6-1: Дискретная СВ")
        self.notebook.add(self.tab2, text="ЛР 6-2: Нормальная СВ")

        self.setup_tab1()
        self.setup_tab2()

    def setup_tab1(self):
        # --- ВВОД ДАННЫХ ---
        input_frame = ttk.LabelFrame(self.tab1, text=" Параметры распределения (X и P) ", padding=10)
        input_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Создаем сетку для ввода (5 пар по умолчанию)
        self.x_entries = []
        self.p_entries = []
        
        # Заголовки мини-таблицы ввода
        ttk.Label(input_frame, text="№", font='bold').grid(row=0, column=0, padx=5)
        ttk.Label(input_frame, text="Значение X", font='bold').grid(row=0, column=1, padx=5)
        ttk.Label(input_frame, text="Вероятность P", font='bold').grid(row=0, column=2, padx=5)

        default_x = [1, 2, 3, 4, 5]
        default_p = [0.1, 0.2, 0.4, 0.2, 0.1]

        for i in range(5):
            ttk.Label(input_frame, text=f"{i+1}").grid(row=i+1, column=0)
            
            ex = ttk.Entry(input_frame, width=15)
            ex.insert(0, str(default_x[i]))
            ex.grid(row=i+1, column=1, padx=5, pady=2)
            self.x_entries.append(ex)
            
            ep = ttk.Entry(input_frame, width=15)
            ep.insert(0, str(default_p[i]))
            ep.grid(row=i+1, column=2, padx=5, pady=2)
            self.p_entries.append(ep)

        btn_run = ttk.Button(input_frame, text="РАССЧИТАТЬ", command=self.run_lab6_1)
        btn_run.grid(row=1, column=3, rowspan=5, padx=20, sticky="nsew")
        ttk.Label(input_frame, text="График для N:").grid(row=1, column=4, sticky=tk.S)
        self.combo_n1 = ttk.Combobox(input_frame, values=["10", "100", "1000", "10000"], width=8, state="readonly")
        self.combo_n1.current(3) # По умолчанию выбрано 10000 (индекс 3)
        self.combo_n1.grid(row=2, column=4, sticky=tk.N)

        # --- ТАБЛИЦА РЕЗУЛЬТАТОВ ---
        self.tree1 = ttk.Treeview(self.tab1, columns=("N", "M_emp", "M_err", "D_emp", "D_err", "Chi2", "Result"), show='headings', height=5)
        self.tree1.heading("N", text="Объем N")
        self.tree1.heading("M_emp", text="M (эмп)")
        self.tree1.heading("M_err", text="M ош (%)")
        self.tree1.heading("D_emp", text="D (эмп)")
        self.tree1.heading("D_err", text="D ош (%)")
        self.tree1.heading("Chi2", text="Хи-квадрат")
        self.tree1.heading("Result", text="Критерий")
        
        # Настройка ширины и выравнивания
        for col in self.tree1['columns']:
            self.tree1.column(col, width=120, anchor=tk.CENTER)
        
        self.tree1.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # --- ГРАФИК ---
        self.fig1, self.ax1 = plt.subplots(figsize=(5, 3))
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.tab1)
        self.canvas1.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def run_lab6_1(self):
        try:
            values = []
            probs = []
            for i in range(len(self.x_entries)):
                vx = self.x_entries[i].get().strip()
                vp = self.p_entries[i].get().strip()
                if vx and vp: # берем только непустые ячейки
                    values.append(float(vx))
                    probs.append(float(vp))

            values = np.array(values)
            probs = np.array(probs)

            if not np.isclose(np.sum(probs), 1.0):
                raise ValueError(f"Сумма вероятностей {np.sum(probs):.3f} != 1.0")

        except ValueError as e:
            messagebox.showerror("Ошибка", f"Проверьте корректность данных: {e}")
            return

        # Очистка таблицы
        for row in self.tree1.get_children():
            self.tree1.delete(row)

        
        n_sizes = [10, 100, 1000, 10000]
        m_teor = np.sum(values * probs) # Теор. среднее = Сумма (X * P)
        d_teor = np.sum(values**2 * probs) - m_teor**2 # Теор. дисперсия E(X^2) - E^2(X)
        
        last_emp_probs = None

        for N in n_sizes:
            # ЗАДАНИЕ 1.1: ГЕНЕРАЦИЯ
            # метод кумулятивных вероятностей
            cum_probs = np.cumsum(probs)
            samples = values[np.searchsorted(cum_probs, np.random.rand(N))]
            
            # ЗАДАНИЕ 1.2: Эмпирические значения
            m_emp = np.mean(samples) # Выборочное среднее
            d_emp = np.var(samples)  # Выборочная дисперсия 
            
            err_m = abs(m_emp - m_teor) / abs(m_teor) * 100 if m_teor != 0 else abs(m_emp)*100 # относительная погрешность мат одидания
            err_d = abs(d_emp - d_teor) / d_teor * 100 if d_teor != 0 else abs(d_emp)*100 # относительная погрешность дисперсии
            
            observed = np.array([np.sum(samples == v) for v in values]) # Сколько выпало реально
            excepted = probs * N

            # По сложной математической формуле она вычисляем число chi_stat (насколько сильно реальность отклонилась от идеала)
            chi_stat, _ = stats.chisquare(observed, f_exp=excepted + 1e-10)

            #  Вычисляет критическое (допустимое) значение ХИ^2 по таблицам математической статистики
            chi_crit = stats.chi2.ppf(0.95, df=len(values)-1)
            status = "ПРОЙДЕН" if chi_stat < chi_crit else "ОТКЛОНЕН"
            
            # Добавление в таблицу
            self.tree1.insert("", tk.END, values=(
                N, f"{m_emp:.3f}", f"{err_m:.1f}%", 
                f"{d_emp:.3f}", f"{err_d:.1f}%", 
                f"{chi_stat:.2f}", status
            ))
            last_emp_probs = observed / N


            if N == int(self.combo_n1.get()):
                self.ax1.clear()
                x_axis = np.arange(len(values))
                self.ax1.bar(x_axis - 0.2, probs, 0.4, label='Теория', alpha=0.6)
                # В легенде теперь пишется актуальное N
                self.ax1.bar(x_axis + 0.2, observed/N, 0.4, label=f'Эмп (N={N})', alpha=0.6)
                self.ax1.set_xticks(x_axis)
                self.ax1.set_xticklabels(values)
                self.ax1.legend()
                self.ax1.set_title(f"Сравнение распределений (N={N})")
                self.canvas1.draw()


    def setup_tab2(self):
        input_frame = ttk.LabelFrame(self.tab2, text=" Параметры нормального распределения ", padding=10)
        input_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Label(input_frame, text="M (mu):").grid(row=0, column=0)
        self.ent_mu = ttk.Entry(input_frame, width=10)
        self.ent_mu.insert(0, "0")
        self.ent_mu.grid(row=0, column=1, padx=5)

        ttk.Label(input_frame, text="Sigma:").grid(row=0, column=2)
        self.ent_sigma = ttk.Entry(input_frame, width=10)
        self.ent_sigma.insert(0, "1")
        self.ent_sigma.grid(row=0, column=3, padx=5)

        btn_run = ttk.Button(input_frame, text="МОДЕЛИРОВАТЬ", command=self.run_lab6_2)
        btn_run.grid(row=0, column=4, padx=20)
        tk.Label(input_frame, text="График для N:").grid(row=0, column=5, padx=5)
        self.combo_n2 = ttk.Combobox(input_frame, values=["10", "100", "1000", "10000"], width=8, state="readonly")
        self.combo_n2.current(3) # По умолчанию 10000
        self.combo_n2.grid(row=0, column=6, padx=5)

        # Таблица результатов
        self.tree2 = ttk.Treeview(self.tab2, columns=("N", "M_emp", "M_err", "D_emp", "D_err", "Chi2", "Result"), show='headings', height=5)
        for col in self.tree2['columns']:
            self.tree2.heading(col, text=col.replace("_", " "))
            self.tree2.column(col, width=120, anchor=tk.CENTER)
        self.tree2.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.fig2, self.ax2 = plt.subplots(figsize=(5, 3))
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.tab2)
        self.canvas2.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def run_lab6_2(self):
        try:
            mu = float(self.ent_mu.get()) #теор среднее
            sigma = float(self.ent_sigma.get()) # теор сигма
        except: return

        for row in self.tree2.get_children(): self.tree2.delete(row)

        # ЗАДАНИЕ 2
        for N in [10, 100, 1000, 10000]:
            # Генерируем два массива по N базовых случайных чисел (от 0 до 1)
            u1, u2 = np.random.rand(N), np.random.rand(N)
            # Применяем математическую формулу Бокса-Мюллера
            samples = np.sqrt(-2 * np.log(u1 + 1e-10)) * np.cos(2 * np.pi * u2) * sigma + mu
            
            # # Эмпирическое среднее и дисперсия 
            m_e, v_e = np.mean(samples), np.var(samples)
            # относительная погрешность
            err_m = abs(m_e - mu) / abs(mu) * 100 if mu != 0 else abs(m_e)*100
            err_v = abs(v_e - sigma**2) / (sigma**2) * 100
            
            # Группировка: разбиваем данные на 10 интервалов (bins=10)
            # counts - сколько чисел попало в каждый интервал
            counts, bins = np.histogram(samples, bins=10)
            
            # Считаем теоретические вероятности попадания в каждый интервал
            cdf_vals = stats.norm.cdf(bins, mu, sigma)
            expected_probs = np.diff(cdf_vals)
            
            # Находим идеальное ожидаемое количество попаданий (expected)
            # НОРМИРОВКА: Сумма expected должна быть равна сумме counts (N)
            # Делим на сумму вероятностей, чтобы они в сумме дали 1.0 внутри наших границ
            expected = (expected_probs / np.sum(expected_probs)) * N

            # Вычисляем саму статистику Хи-квадрат и сравниваем с критическим значением
            chi_stat, _ = stats.chisquare(counts, f_exp=expected)

            # Выносим вердикт
            status = "ПРОЙДЕН" if chi_stat < stats.chi2.ppf(0.95, 9) else "ОТКЛОНЕН"

            self.tree2.insert("", tk.END, values=(N, f"{m_e:.3f}", f"{err_m:.1f}%", f"{v_e:.3f}", f"{err_v:.1f}%", f"{chi_stat:.2f}", status))

            if N == int(self.combo_n2.get()):
                self.ax2.clear()
                self.ax2.hist(samples, bins=30, density=True, alpha=0.5, color='g', label='Эмпирика')
                x_plot = np.linspace(mu-4*sigma, mu+4*sigma, 100)
                self.ax2.plot(x_plot, stats.norm.pdf(x_plot, mu, sigma), 'r', label='Теория')
                self.ax2.set_title(f"Гистограмма и плотность (N={N})")
                self.ax2.legend()
                self.canvas2.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = LabWorkApp(root)
    root.mainloop()