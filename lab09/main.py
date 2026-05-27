import numpy as np
import tkinter as tk
from tkinter import messagebox, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class MM1LossSimulation:
    def __init__(self, lambd, mu, max_time):
        self.lambd = lambd 
        self.mu = mu 
        self.max_time = max_time
        
        # Состояние системы
        self.t = 0  
        self.x = 0 # 0 - свободно, 1 - занято. Очереди (y) нет.
        
        # Статистика
        self.system_states = [] 
        self.total_customers = 0
        self.lost_customers = 0

    def run(self):
        tau = np.random.exponential(1/self.lambd) 
        delta = float('inf') 
        
        while self.t < self.max_time:
            # Сохраняем состояние (только x, так как y = 0)
            self.system_states.append((self.t, self.x))
            
            if tau < delta:
                # СОБЫТИЕ: Появление клиента
                self.t += tau
                self.total_customers += 1
                
                if self.x == 0:
                    self.x = 1
                    delta = np.random.exponential(1/self.mu)
                else:
                    # ОЧЕРЕДИ НЕТ: Клиент уходит (отказ)
                    self.lost_customers += 1
                
                tau = np.random.exponential(1/self.lambd)
            else:
                # СОБЫТИЕ: (обслуживание завершается раньше, чем приходит новый клиент)
                self.t += delta
                tau -= delta
                
                self.x = 0 
                delta = float('inf')

        return self.system_states, self.total_customers, self.lost_customers

    def get_distribution_data(self):
        total_times = {0: 0, 1: 0} 
        for i in range(len(self.system_states) - 1): # Цикл проходит по всем сохраненным состояниям
            start_t, count = self.system_states[i]
            end_t, _ = self.system_states[i+1]
            duration = end_t - start_t
            total_times[count] = total_times.get(count, 0) + duration
            
        counts = sorted(total_times.keys())
        probs = [total_times[c] / self.t for c in counts] # расчет относительных частот (эмпирических вероятностей)
        return counts, probs


class SimulationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Модель M/M/1/0 (Система с отказами, без очереди)")
        self.root.geometry("1100x750")

        control_frame = tk.Frame(root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        params = [("λ (вход):", "2.0"), ("μ (обслуж.):", "2.5"), ("Время:", "1000")]
        self.entries = {}
        for i, (label, default) in enumerate(params):
            tk.Label(control_frame, text=label).grid(row=0, column=i*2, padx=5)
            entry = tk.Entry(control_frame, width=8)
            entry.insert(0, default)
            entry.grid(row=0, column=i*2+1, padx=5)
            self.entries[label] = entry

        btn_run = tk.Button(control_frame, text="РАССЧИТАТЬ", command=self.run_simulation, 
                            bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        btn_run.grid(row=0, column=6, padx=20)

        table_frame = tk.Frame(root)
        table_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.tree = ttk.Treeview(table_frame, columns=("param", "theory", "practice"), show='headings', height=5)
        self.tree.heading("param", text="Параметр")
        self.tree.heading("theory", text="Теория (Эрланг)")
        self.tree.heading("practice", text="Практика (Имитация)")
        self.tree.column("param", width=300, anchor="center")
        self.tree.pack(fill=tk.X)

        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def run_simulation(self):
        try:
            l = float(self.entries["λ (вход):"].get())
            m = float(self.entries["μ (обслуж.):"].get())
            t_max = float(self.entries["Время:"].get())

            sim = MM1LossSimulation(l, m, t_max)
            states, total, lost = sim.run()
            counts, probs = sim.get_distribution_data()

            # --- ТЕОРИЯ M/M/1/0 (Формулы Эрланга) ---
            rho = l / m
            p0_theory = 1 / (1 + rho)           # Вер-ть простоя
            p_loss_theory = rho / (1 + rho)     # Вер-ть отказа (она же P1)
            L_theory = p_loss_theory            # Ср. число клиентов (т.к. макс 1)

            # --- ПРАКТИКА ---
            p0_prac = probs[0] if 0 in counts else 0
            p_loss_prac = lost / total if total > 0 else 0
            L_prac = sum(n * p for n, p in zip(counts, probs))

            for i in self.tree.get_children(): self.tree.delete(i)
            
            res = [
                ("Интенсивность нагрузки (ρ)", f"{rho:.3f}", f"---"),
                ("Вероятность простоя (P0)", f"{p0_theory:.3f}", f"{p0_prac:.3f}"),
                ("Вероятность отказа (P_loss)", f"{p_loss_theory:.3f}", f"{p_loss_prac:.3f}"),
                ("Среднее число клиентов (L)", f"{L_theory:.3f}", f"{L_prac:.3f}")
            ]
            for r in res: self.tree.insert("", "end", values=r)

            self.ax1.clear()
            self.ax1.bar(counts, probs, color='blue', alpha=0.6, label='Практика')
            self.ax1.set_xticks([0, 1])
            self.ax1.set_title("Распределение клиентов (0 или 1)")
            self.ax1.set_ylabel("Вероятность")
            self.ax1.grid(axis='y')

            self.ax2.clear()
            labels = ['Обслужено', 'Упущено (отказ)']
            sizes = [total - lost, lost]
            self.ax2.pie(sizes, labels=labels, autopct='%1.1f%%', colors=['#66b3ff','#ff9999'], startangle=90)
            self.ax2.set_title("Соотношение клиентов")

            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationGUI(root)
    root.mainloop()