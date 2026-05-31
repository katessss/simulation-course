import heapq
import queue
import random
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Dict, List, Optional

# Интеграция графиков Matplotlib в Tkinter
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class Customer:

    def __init__(
        self, cid: int, arrival_time: float, service_time: float, patience: float):
        self.id: int = cid
        self.arrival_time: float = arrival_time
        self.service_time: float = service_time
        self.patience: float = patience
        self.reneging_time: float = arrival_time + patience

        self.start_service_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.status: str = "created"  # served, reneged, blocked, in_queue


class Event:
    # описывает изменение состояния системы в фиксированный момент времени
    ARRIVAL = 0 # Прибытие новой заявки
    DEPARTURE = 1 # Завершение обслуживания заявки на приборе
    RENEGING = 2 # Истечение терпения заявки в очеред

    def __init__(self, time: float, event_type: int, customer: Customer):
        self.time: float = time
        self.type: int = event_type
        self.customer: Customer = customer

    def __lt__(self, other: "Event") -> bool:
        return self.time < other.time


class TheoreticalCalculator:
    # Расчет аналитических характеристик СМО M/M/c/K с нетерпеливостью
    # p[n] - это вероятность того, что в случайный момент времени в системе (на обслуживании + в очереди) будет находиться ровно n заявок

    @staticmethod
    def calculate(lam: float, mu: float, c: int, K: int, theta: float) -> Dict[str, float]:
        total_states = c + K + 1 # общее количество возможных состояний системы
        p = [0.0] * total_states
        p[0] = 1.0

        for n in range(1, total_states): # интенсивности ухода 
            if n <= c:
                dep_rate = n * mu
            else:
                dep_rate = c * mu + (n - c) * theta

            if dep_rate > 0:
                p[n] = p[n - 1] * (lam / dep_rate) # уравнение Колмогорова
            else:
                p[n] = 0.0

        # нормировка
        sum_p = sum(p)
        if sum_p > 0:
            p = [x / sum_p for x in p]
        else:
            p[0] = 1.0

        # вероятность отказа
        p_block = p[c + K]
        L_q = sum((n - c) * p[n] for n in range(c, total_states)) # средняя лдина очереди
        lam_eff = lam * (1.0 - p_block)
        renege_rate = sum((n - c) * theta * p[n] for n in range(c, total_states))

        p_renege = renege_rate / lam if lam > 0 else 0.0 # вероятность ухода
        p_served = 1.0 - p_block - p_renege
        avg_wait_time = L_q / lam_eff if lam_eff > 0 else 0.0 # среднее время ожидания: W = L/lam_eff

        return {
            "p_block": p_block, # p[c+K]
            "p_renege": p_renege, # renege_rate / lam 
            "p_served": p_served, # 1 - p_block - p_renege
            "avg_wait_time": avg_wait_time, # W = L/lam_eff
            "avg_queue_length": L_q, # мат ожидание (сумма значений длины очереди (n-c)*p_n (вероятность нахождения в системе))
        }


class QueueSystemSimulator:

    def __init__(
        self,
        num_servers: int, # c
        queue_capacity: int, # K
        arrival_rate: float, # lambda
        service_rate: float, # mu
        patience_rate: float, # teta (Интенсивность ухода по нетерпеливости)
        sim_duration: float, # T
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        self.num_servers: int = num_servers
        self.queue_capacity: int = queue_capacity
        self.arrival_rate: float = arrival_rate
        self.service_rate: float = service_rate
        self.patience_rate: float = patience_rate
        self.sim_duration: float = sim_duration
        self.log_callback: Optional[Callable[[str], None]] = log_callback

        self.current_time: float = 0.0
        self.event_queue: List[Event] = [] # календарь событий
        self.queue: List[Customer] = [] # челы в очереди ФИФО
        self.busy_servers: int = 0

        self.queue_history: List[tuple] = [(0.0, 0)] # (модельное время, длина очереди)
        self.customers: List[Customer] = [] # Архив клиентов
        self.stats = {
            "total_arrivals": 0, # прибывшие
            "served": 0, # успешно обслуженное
            "blocked": 0, # отказ из-за переполнения очереди 
            "reneged": 0, # ушли сами
        }

    def _log(self, text: str):
        if self.log_callback:
            self.log_callback(text)

    def _schedule_event(self, time: float, event_type: int, customer: Customer):
        heapq.heappush(self.event_queue, Event(time, event_type, customer))

    def _record_queue_length(self):
        self.queue_history.append((self.current_time, len(self.queue)))

    def _generate_customer(self, cid: int, arrival_time: float) -> Customer:
        service_time = random.expovariate(self.service_rate)
        patience = (
            random.expovariate(self.patience_rate)
            if self.patience_rate > 0 else 1e9
        )
        return Customer(cid, arrival_time, service_time, patience)

    def run(self) -> Dict[str, float]:
        first_arrival = self.current_time + random.expovariate(self.arrival_rate)
        first_cust = self._generate_customer(1, first_arrival)
        self._schedule_event(first_arrival, Event.ARRIVAL, first_cust)
        next_id = 2

        while self.event_queue:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time

            if self.current_time > self.sim_duration:
                break

            if event.type == Event.ARRIVAL:
                self._handle_arrival(event.customer)
                next_arrival = self.current_time + random.expovariate(self.arrival_rate)
                next_cust = self._generate_customer(next_id, next_arrival)
                self._schedule_event(next_arrival, Event.ARRIVAL, next_cust)
                next_id += 1

            elif event.type == Event.DEPARTURE:
                self._handle_departure(event.customer)

            elif event.type == Event.RENEGING:
                self._handle_reneging(event.customer)

        return self._calculate_empirical_results()

    def _handle_arrival(self, customer: Customer):
        self.stats["total_arrivals"] += 1
        self.customers.append(customer)

        self._log(f"[{self.current_time:.2f}]: Заявка #{customer.id} поступила.")

        if self.busy_servers < self.num_servers: # есть свободный прибор
            self.busy_servers += 1
            customer.start_service_time = self.current_time
            customer.status = "served"
            self._schedule_event(
                self.current_time + customer.service_time,
                Event.DEPARTURE,
                customer,
            )
            self._log(f"[{self.current_time:.2f}]: Заявка #{customer.id} заняла прибор.")

        elif len(self.queue) < self.queue_capacity: # занято, но есть место в очереди
            customer.status = "in_queue"
            self.queue.append(customer)
            self._record_queue_length()
            self._schedule_event(customer.reneging_time, Event.RENEGING, customer)
            self._log(f"[{self.current_time:.2f}]: Заявка #{customer.id} встала в очередь (Очередь: {len(self.queue)}).")
        
        else: # приборы и очередь заняты
            customer.status = "blocked"
            customer.end_time = self.current_time
            self.stats["blocked"] += 1
            self._log(f"[{self.current_time:.2f}]: Очередь полна. Заявка #{customer.id} отклонена.")

    def _handle_departure(self, customer: Customer):
        customer.end_time = self.current_time
        self.busy_servers -= 1
        self.stats["served"] += 1
        self._log(f"[{self.current_time:.2f}]: Заявка #{customer.id} обслужена.")

        if self.queue:
            next_cust = self.queue.pop(0)
            self._record_queue_length()
            self.busy_servers += 1
            next_cust.start_service_time = self.current_time
            next_cust.status = "served"
            self._schedule_event(
                self.current_time + next_cust.service_time,
                Event.DEPARTURE,
                next_cust,
            )
            self._log(f"[{self.current_time:.2f}]: Заявка #{next_cust.id} покинула очередь и начала обслуживаться.")

    def _handle_reneging(self, customer: Customer):
        if customer in self.queue:
            self.queue.remove(customer)
            self._record_queue_length()
            customer.status = "reneged"
            customer.end_time = self.current_time
            self.stats["reneged"] += 1
            self._log(f"[{self.current_time:.2f}]: Заявка #{customer.id} потеряла терпение и ушла.")

    def _calculate_empirical_results(self) -> Dict[str, float]:
        # подсчёт статистики
        total = self.stats["total_arrivals"]
        if total == 0:
            return {
                "p_block": 0.0,
                "p_renege": 0.0,
                "p_served": 0.0,
                "avg_wait_time": 0.0,
                "avg_queue_length": 0.0,
            }

        # среднее время ожидание 
        accepted_custs = [c for c in self.customers if c.status in ("served", "reneged")]
        total_wait = 0.0
        for c in accepted_custs:
            end_wait = c.start_service_time if c.start_service_time is not None else c.end_time
            total_wait += (end_wait - c.arrival_time)
        avg_wait_time = total_wait / len(accepted_custs) if accepted_custs else 0.0

        # средняя длина очереди
        total_duration = min(self.sim_duration, self.current_time)
        weighted_queue_sum = 0.0
        for i in range(len(self.queue_history) - 1):
            t1, q1 = self.queue_history[i]
            t2, _ = self.queue_history[i + 1]
            weighted_queue_sum += q1 * (t2 - t1)

        if self.queue_history:
            last_t, last_q = self.queue_history[-1]
            if total_duration > last_t:
                weighted_queue_sum += last_q * (total_duration - last_t)

        avg_queue_len = (
            weighted_queue_sum / total_duration if total_duration > 0 else 0.0
        )

        return {
            "p_block": self.stats["blocked"] / total,
            "p_renege": self.stats["reneged"] / total,
            "p_served": self.stats["served"] / total,
            "avg_wait_time": avg_wait_time,
            "avg_queue_length": avg_queue_len,
        }


# КЛАСС GUI (ИНТЕГРИРОВАННЫЙ ДАШБОРД)

class SimulationGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Симулятор СМО M/M/c/K с нетерпеливостью")

        # Размер адаптирован для бесконфликтного размещения всех элементов
        self.root.geometry("980x720")
        self.root.resizable(False, False)

        self.log_queue = queue.Queue()
        self._create_widgets()

        self.log_file = open("simulation_gui_log.txt", "w", encoding="utf-8")
        self.root.after(100, self._process_log_queue)

    def _create_widgets(self):
        # Основной горизонтальный контейнер
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ---------------- Левая панель параметров ----------------
        left_frame = ttk.LabelFrame(main_paned, text=" Параметры ", padding=8)
        main_paned.add(left_frame, weight=1)

        self.params = {}
        fields = [
            ("Поток заявок (λ):", "lambda", "3.0"),
            ("Обслуживание (μ):", "mu", "1.0"),
            ("Каналы (c):", "c", "2"),
            ("Очередь (K):", "K", "3"),
            ("Уход по нетерп. (θ):", "theta", "0.5"),
            ("Время работы (T):", "duration", "1000.0"),
        ]

        for i, (label, name, default) in enumerate(fields):
            lbl = ttk.Label(left_frame, text=label, font=("Arial", 9))
            lbl.grid(row=i, column=0, sticky=tk.W, pady=4)
            entry = ttk.Entry(left_frame, width=10, font=("Arial", 9))
            entry.insert(0, default)
            entry.grid(row=i, column=1, sticky=tk.E, pady=4)
            self.params[name] = entry

        self.btn_run = ttk.Button(
            left_frame, text="Запустить расчет", command=self._start_simulation
        )
        self.btn_run.grid(row=len(fields), column=0, columnspan=2, pady=15, sticky=tk.EW)

        # ---------------- Правая панель (Дашборд без вкладок) ----------------
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=4)

        # 1. Верхняя секция: Таблица сравнения
        table_frame = ttk.LabelFrame(right_frame, text=" Сравнительный анализ показателей СМО ", padding=5)
        table_frame.pack(fill=tk.X, side=tk.TOP, pady=3)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("metric", "theoretical", "empirical", "diff"),
            show="headings",
            height=5,  # компактная таблица на 5 строк
        )
        self.tree.heading("metric", text="Параметр")
        self.tree.heading("theoretical", text="Теория (Эрланг)")
        self.tree.heading("empirical", text="Практика (Имитация)")
        self.tree.heading("diff", text="Разница")

        self.tree.column("metric", width=240, anchor=tk.W)
        self.tree.column("theoretical", width=120, anchor=tk.CENTER)
        self.tree.column("empirical", width=120, anchor=tk.CENTER)
        self.tree.column("diff", width=100, anchor=tk.CENTER)
        self.tree.pack(fill=tk.X, expand=True)

        # 2. Средняя секция: Графики Matplotlib
        charts_frame = ttk.LabelFrame(right_frame, text=" Аналитические графики ")
        charts_frame.pack(fill=tk.BOTH, expand=True, pady=3)

        # Геометрия графиков адаптирована под горизонтальное расположение
        self.fig = Figure(figsize=(7.0, 2.8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=charts_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        # 3. Нижняя секция: Текстовый лог
        log_frame = ttk.LabelFrame(right_frame, text=" Детализированный лог событий ")
        log_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=3)

        # Высота лога уменьшена до 6 строк для компактности
        self.txt_log = tk.Text(
            log_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 8), height=6
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=3, pady=3)

        scrollbar = ttk.Scrollbar(log_frame, command=self.txt_log.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.txt_log.config(yscrollcommand=scrollbar.set)

    def _queue_logger(self, text: str):
        self.log_queue.put(text)

    def _process_log_queue(self):
        """Оптимизированная обработка логов порциями."""
        self.txt_log.config(state=tk.NORMAL)
        processed = 0
        while processed < 100:
            try:
                text = self.log_queue.get_nowait()
                self.txt_log.insert(tk.END, text + "\n")
                processed += 1
            except queue.Empty:
                break

        if processed > 0:
            self.txt_log.see(tk.END)

        self.txt_log.config(state=tk.DISABLED)
        self.root.after(30, self._process_log_queue)

    def _start_simulation(self):
        try:
            lam = float(self.params["lambda"].get())
            mu = float(self.params["mu"].get())
            c = int(self.params["c"].get())
            K = int(self.params["K"].get())
            theta = float(self.params["theta"].get())
            duration = float(self.params["duration"].get())

            if min(lam, mu, c, K, duration) < 0 or theta < 0:
                raise ValueError("Параметры должны быть положительными.")
            if c <= 0:
                raise ValueError("Необходимо минимум 1 канал обслуживания (c >= 1).")

        except ValueError as e:
            messagebox.showerror(
                "Ошибка ввода", f"Пожалуйста, проверьте параметры.\nОписание: {e}"
            )
            return

        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.delete("1.0", tk.END)
        self.txt_log.config(state=tk.DISABLED)
        self.btn_run.config(state=tk.DISABLED)

        # Запуск симуляции в фоне
        sim_thread = threading.Thread(
            target=self._run_async, args=(lam, mu, c, K, theta, duration)
        )
        sim_thread.daemon = True
        sim_thread.start()

    def _run_async(self, lam, mu, c, K, theta, duration):
        theory = TheoreticalCalculator.calculate(lam, mu, c, K, theta)

        self.log_file.seek(0)
        self.log_file.truncate()

        # Если T > 200, в окно логов шлем только системное предупреждение, чтобы не перегружать интерфейс
        use_gui_logging = duration <= 200

        if not use_gui_logging:
            self._queue_logger(
                f"[Система]: Логирование в UI приостановлено для T={duration}. "
                "Полный лог записывается в файл simulation_gui_log.txt"
            )

        def log_handler(text):
            try:
                self.log_file.write(text + "\n")
            except Exception:
                pass
            if use_gui_logging:
                self._queue_logger(text)

        sim = QueueSystemSimulator(
            num_servers=c,
            queue_capacity=K,
            arrival_rate=lam,
            service_rate=mu,
            patience_rate=theta,
            sim_duration=duration,
            log_callback=log_handler,
        )

        empirical = sim.run()
        queue_hist = sim.queue_history

        self.log_file.flush()

        # Передача результатов обратно в главный поток GUI
        self.root.after(
            0, self._update_ui_results, theory, empirical, queue_hist
        )

    def _update_ui_results(self, theory, empirical, queue_hist):
        # 1. Обновление таблицы показателей
        for row in self.tree.get_children():
            self.tree.delete(row)

        metrics_mapping = [
            ("Вероятность отказа (P_отк)", theory["p_block"], empirical["p_block"], "{:.4f}"),
            ("Доля обслуженных (P_обслуж)", theory["p_served"], empirical["p_served"], "{:.4f}"),
            ("Доля ухода по нетерп. (P_ухода)", theory["p_renege"], empirical["p_renege"], "{:.4f}"),
            ("Время ожидания в очереди (W_q)", theory["avg_wait_time"], empirical["avg_wait_time"], "{:.3f}"),
            ("Средняя длина очереди (L_q)", theory["avg_queue_length"], empirical["avg_queue_length"], "{:.3f}"),
        ]

        for name, t_val, e_val, fmt in metrics_mapping:
            diff = abs(t_val - e_val)
            self.tree.insert(
                "",
                tk.END,
                values=(
                    name,
                    fmt.format(t_val),
                    fmt.format(e_val),
                    fmt.format(diff),
                ),
            )

        # 2. Обновление графиков
        self._draw_graphs(theory, empirical, queue_hist)

        self.btn_run.config(state=tk.NORMAL)
        # messagebox.showinfo("Готово", "Моделирование успешно завершено.")

    def _draw_graphs(self, theory, empirical, queue_hist):
        self.fig.clear()

        # Левый график: Вероятности исходов
        ax1 = self.fig.add_subplot(121)
        categories = ["Обслужено", "Отказ", "Уход"]
        theory_data = [theory["p_served"], theory["p_block"], theory["p_renege"]]
        empirical_data = [empirical["p_served"], empirical["p_block"], empirical["p_renege"]]

        x = range(len(categories))
        width = 0.3

        ax1.bar([i - width / 2 for i in x], theory_data, width, label="Теория", color="#3b5998")
        ax1.bar([i + width / 2 for i in x], empirical_data, width, label="Имитация", color="#e06666")

        ax1.set_ylabel("Вероятность", fontsize=8)
        ax1.set_title("Сравнение распределения исходов", fontsize=9, fontweight="bold")
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories, fontsize=8)
        ax1.legend(fontsize=8)
        ax1.grid(True, linestyle=":", alpha=0.6)

        # Правый график: Процесс изменения длины очереди (первые 100 изменений)
        ax2 = self.fig.add_subplot(122)
        if queue_hist:
            plot_points = queue_hist[:100]
            times, lengths = zip(*plot_points)

            ax2.step(times, lengths, where="post", color="#2ca02c", linewidth=1.5)
            ax2.set_xlabel("Модельное время", fontsize=8)
            ax2.set_ylabel("Размер очереди", fontsize=8)
            ax2.set_title("Динамика очереди (до 100 событий)", fontsize=9, fontweight="bold")
            ax2.grid(True, linestyle=":", alpha=0.6)

        self.fig.tight_layout()
        self.canvas.draw()

    def __del__(self):
        if hasattr(self, "log_file") and not self.log_file.closed:
            self.log_file.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationGUI(root)
    root.mainloop()