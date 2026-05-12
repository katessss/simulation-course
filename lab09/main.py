import numpy as np
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class MM1Simulation:
    def __init__(self, lambd, mu, max_time):
        self.lambd = lambd  # Интенсивность входящего потока
        self.mu = mu        # Интенсивность обслуживания
        self.max_time = max_time
        
        # Состояние системы
        self.t = 0          # Текущее модельное время
        self.x = 0          # Клиентов на обслуживании (0 или 1 для M/M/1)
        self.y = 0          # Клиентов в очереди
        
        # Статистика
        self.wait_times = []      # Время пребывания каждого клиента в очереди
        self.system_states = []   # (время, кол-во клиентов в системе)
        self.arrival_times = []   # Временные метки прибытия клиентов в очередь

    def run(self):
        # Начальная генерация событий (Слайд 10, шаг 2)
        tau = np.random.exponential(1/self.lambd) # Время до появления клиента
        delta = float('inf')                      # Время до окончания обслуживания
        
        while self.t < self.max_time:
            # Сохраняем текущее состояние системы для статистики
            self.system_states.append((self.t, self.x + self.y))
            
            # Слайд 10, шаг 4: выбор ближайшего события
            if tau < delta:
                # СОБЫТИЕ: Появление клиента
                self.t += tau
                delta -= tau # Уменьшаем оставшееся время обслуживания
                
                if self.x < 1: # Если оператор свободен (N=1 для ПВЗ)
                    self.x = 1
                    self.wait_times.append(0) # Клиент сразу идет на обслуживание
                    delta = np.random.exponential(1/self.mu)
                else:
                    self.y += 1 # В очередь
                    self.arrival_times.append(self.t)
                
                tau = np.random.exponential(1/self.lambd)
            else:
                # СОБЫТИЕ: Окончание обслуживания
                self.t += delta
                tau -= delta # Уменьшаем время до нового прибытия
                
                if self.y == 0:
                    self.x = 0
                    delta = float('inf')
                else:
                    self.y -= 1
                    # Клиент из очереди идет на обслуживание
                    arrival = self.arrival_times.pop(0)
                    self.wait_times.append(self.t - arrival)
                    delta = np.random.exponential(1/self.mu)

        return self.wait_times, self.system_states

    def get_distribution_data(self):
        # Расчет среднего времени пребывания системы в каждом состоянии (N клиентов)
        total_times = {}
        for i in range(len(self.system_states) - 1):
            start_t, count = self.system_states[i]
            end_t, _ = self.system_states[i+1]
            duration = end_t - start_t
            total_times[count] = total_times.get(count, 0) + duration
            
        # Вероятности нахождения n клиентов в системе
        counts = sorted(total_times.keys())
        probs = [total_times[c] / self.t for c in counts]
        return counts, probs




class SimulationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Моделирование ПВЗ (M/M/1)")
        
        # Панель управления
        control_frame = tk.Frame(root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Label(control_frame, text="λ (прибытие):").grid(row=0, column=0)
        self.entry_lambda = tk.Entry(control_frame)
        self.entry_lambda.insert(0, "2.0")
        self.entry_lambda.grid(row=0, column=1)
        
        tk.Label(control_frame, text="μ (обслуживание):").grid(row=0, column=2)
        self.entry_mu = tk.Entry(control_frame)
        self.entry_mu.insert(0, "2.5")
        self.entry_mu.grid(row=0, column=3)
        
        tk.Label(control_frame, text="Время модел.:").grid(row=0, column=4)
        self.entry_time = tk.Entry(control_frame)
        self.entry_time.insert(0, "1000")
        self.entry_time.grid(row=0, column=5)
        
        btn_run = tk.Button(control_frame, text="Запустить", command=self.run_simulation)
        btn_run.grid(row=0, column=6, padx=10)

        # Область для графиков
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def run_simulation(self):
        try:
            l = float(self.entry_lambda.get())
            m = float(self.entry_mu.get())
            t_max = float(self.entry_time.get())
            
            sim = MM1Simulation(l, m, t_max)
            wait_times, states = sim.run()
            counts, probs = sim.get_distribution_data()
            
            # Очистка и отрисовка
            self.ax1.clear()
            self.ax2.clear()
            
            # 1. Полигон частот (Число клиентов в системе)
            self.ax1.plot(counts, probs, marker='o', linestyle='-', color='b')
            self.ax1.set_title("Эмпирическое распределение числа клиентов")
            self.ax1.set_xlabel("Количество клиентов (n)")
            self.ax1.set_ylabel("Вероятность P(n)")
            self.ax1.grid(True)

            # 2. Гистограмма (Время ожидания в очереди)
            self.ax2.hist(wait_times, bins=30, density=True, color='green', alpha=0.7)
            self.ax2.set_title("Распределение времени в очереди")
            self.ax2.set_xlabel("Время ожидания (t)")
            self.ax2.set_ylabel("Плотность")
            self.ax2.grid(True)
            
            self.fig.tight_layout()
            self.canvas.draw()
            
            # Вывод кратких итогов
            avg_wait = sum(wait_times)/len(wait_times) if wait_times else 0
            messagebox.showinfo("Результат", f"Среднее время ожидания: {avg_wait:.2f}\n"
                                             f"Загрузка системы (ρ): {l/m:.2f}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationGUI(root)
    root.mainloop()