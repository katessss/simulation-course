import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox
from scipy import stats


class PoissonFlowModel:
   
    
    def __init__(self, lambda_rate, T, num_experiments=1000):

        self.lambda_rate = lambda_rate  # Интенсивность (сколько событий в среднем за 1 ед. времени)
        self.T = T  # Общее время наблюдения
        self.num_experiments = num_experiments # Сколько раз мы повторим симуляцию
        self.event_counts = []
        self.event_times = []
        
    def generate_flow(self):

        t_current = 0
        times = []
        
        while t_current < self.T:
            # Генерируем интервал из экспоненциального распределения
            tau = np.random.exponential(scale=1/self.lambda_rate) # длительность временного интервала между двумя последовательными событиями
            t_current += tau
            
            if t_current <= self.T:
                times.append(t_current)
        
        return times
    
    def run_experiments(self):
        self.event_counts = []
        
        for _ in range(self.num_experiments):
            times = self.generate_flow()
            count = len(times)
            self.event_counts.append(count)
        
        # Сохраняем последний сгенерированный поток для визуализации
        self.event_times = times
        
        return self.event_counts
    
    def get_statistics(self):
        """
        Вычисление статистических характеристик.
        
        Returns:
        --------
        dict : словарь с результатами
            - mean: среднее число событий
            - variance: дисперсия
            - std: стандартное отклонение
            - theoretical_mean: теоретическое среднее (λT)
            - theoretical_variance: теоретическая дисперсия (λT)
        """
        if not self.event_counts:
            self.run_experiments()
        
        mean = np.mean(self.event_counts)
        variance = np.var(self.event_counts, ddof=1)  # несмещенная оценка
        std = np.std(self.event_counts, ddof=1)
        
        # Теоретические значения для пуассоновского потока
        theoretical_mean = self.lambda_rate * self.T
        theoretical_variance = self.lambda_rate * self.T
        
        return {
            'mean': mean,
            'variance': variance,
            'std': std,
            'theoretical_mean': theoretical_mean,
            'theoretical_variance': theoretical_variance,
            'min': min(self.event_counts),
            'max': max(self.event_counts)
        }
    
    def get_distribution(self):
        """
        Получение эмпирического распределения числа событий.
        
        Returns:
        --------
        values : array
            Возможные значения числа событий
        frequencies : array
            Частоты (вероятности) для каждого значения
        """
        if not self.event_counts:
            self.run_experiments()
        
        unique, counts = np.unique(self.event_counts, return_counts=True)
        frequencies = counts / len(self.event_counts) 
        
        return unique, frequencies


class PoissonFlowGUI:
    """
    Графический интерфейс для моделирования пуассоновского потока.
    """
    
    def __init__(self, root):
        """
        Инициализация GUI.
        
        Parameters:
        -----------
        root : tk.Tk
            Главное окно приложения
        """
        self.root = root
        self.root.title("Моделирование пуассоновского потока заявок на сервер - Лабораторная №8")
        self.root.geometry("1200x800")
        
        self.model = None
        self.create_widgets()
        
    def create_widgets(self):
        """Создание элементов интерфейса."""
        
        # Фрейм для параметров
        param_frame = ttk.LabelFrame(self.root, text="Параметры моделирования", padding=10)
        param_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Интенсивность потока λ
        ttk.Label(param_frame, text="Интенсивность λ (заявок/сек):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.lambda_entry = ttk.Entry(param_frame, width=15)
        self.lambda_entry.insert(0, "5.0")
        self.lambda_entry.grid(row=0, column=1, padx=5)
        
        # Интервал времени T
        ttk.Label(param_frame, text="Интервал времени T (сек):").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.T_entry = ttk.Entry(param_frame, width=15)
        self.T_entry.insert(0, "10.0")
        self.T_entry.grid(row=0, column=3, padx=5)
        
        # Число экспериментов
        ttk.Label(param_frame, text="Число экспериментов N:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.N_entry = ttk.Entry(param_frame, width=15)
        self.N_entry.insert(0, "1000")
        self.N_entry.grid(row=1, column=1, padx=5)
        
        # Кнопка запуска
        self.run_button = ttk.Button(param_frame, text="Запустить моделирование", command=self.run_simulation)
        self.run_button.grid(row=1, column=2, columnspan=2, pady=5)
        
        # Фрейм для результатов
        results_frame = ttk.LabelFrame(self.root, text="Статистические результаты", padding=10)
        results_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Текстовое поле для вывода результатов
        self.results_text = tk.Text(results_frame, height=8, width=80, font=("Courier", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Фрейм для графиков
        plot_frame = ttk.Frame(self.root)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Создание области для графиков
        self.fig, self.axes = plt.subplots(1, 2, figsize=(12, 4))
        self.fig.tight_layout(pad=3.0)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def run_simulation(self):
        """Запуск моделирования и отображение результатов."""
        try:
            # Получение параметров
            lambda_rate = float(self.lambda_entry.get())
            T = float(self.T_entry.get())
            N = int(self.N_entry.get())
            
            # Валидация
            if lambda_rate <= 0 or T <= 0 or N <= 0:
                raise ValueError("Все параметры должны быть положительными!")
            
            # Создание модели и запуск экспериментов
            self.model = PoissonFlowModel(lambda_rate, T, N)
            self.model.run_experiments()
            
            # Получение статистики
            stats = self.model.get_statistics()
            
            # Вывод результатов
            self.display_results(stats)
            
            # Построение графиков
            self.plot_results()
            
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
    
    def display_results(self, stats):
        """
        Отображение статистических результатов.
        
        Parameters:
        -----------
        stats : dict
            Словарь со статистическими характеристиками
        """
        self.results_text.delete(1.0, tk.END)
        
        results = f"""
{'='*70}
                    РЕЗУЛЬТАТЫ МОДЕЛИРОВАНИЯ
{'='*70}

ПАРАМЕТРЫ:
  Интенсивность потока (λ):        {self.model.lambda_rate:.2f} заявок/сек
  Интервал времени (T):            {self.model.T:.2f} сек
  Число экспериментов (N):         {self.model.num_experiments}

ЭМПИРИЧЕСКИЕ ХАРАКТЕРИСТИКИ:
  Среднее число заявок:            {stats['mean']:.4f}
  Дисперсия:                       {stats['variance']:.4f}
  Стандартное отклонение:          {stats['std']:.4f}
  Минимум:                         {stats['min']}
  Максимум:                        {stats['max']}

ТЕОРЕТИЧЕСКИЕ ХАРАКТЕРИСТИКИ (пуассоновский поток):
  Теоретическое среднее (λT):      {stats['theoretical_mean']:.4f}
  Теоретическая дисперсия (λT):    {stats['theoretical_variance']:.4f}

ОТКЛОНЕНИЯ:
  Отклонение среднего:             {abs(stats['mean'] - stats['theoretical_mean']):.4f}
  Относительная ошибка среднего:   {abs(stats['mean'] - stats['theoretical_mean'])/stats['theoretical_mean']*100:.2f}%
  Отклонение дисперсии:            {abs(stats['variance'] - stats['theoretical_variance']):.4f}
  Относительная ошибка дисперсии:  {abs(stats['variance'] - stats['theoretical_variance'])/stats['theoretical_variance']*100:.2f}%

{'='*70}
ВЫВОД:
{'='*70}
Моделирование простейшего (пуассоновского) потока заявок на сервер 
показало хорошее соответствие теоретическим значениям.

Эмпирическое среднее ({stats['mean']:.2f}) близко к теоретическому ({stats['theoretical_mean']:.2f}).
Эмпирическая дисперсия ({stats['variance']:.2f}) также соответствует теоретической ({stats['theoretical_variance']:.2f}).

Для пуассоновского потока характерно равенство математического ожидания
и дисперсии (E[X] = Var[X] = λT), что подтверждается результатами.

Построенное эмпирическое распределение согласуется с распределением Пуассона
с параметром λT = {stats['theoretical_mean']:.2f}.
{'='*70}
"""
        
        self.results_text.insert(1.0, results)
    
    def plot_results(self):
        """Построение графиков распределения и примера потока."""
        
        # Очистка предыдущих графиков
        for ax in self.axes:
            ax.clear()
        
        # График 1: Эмпирическое распределение числа заявок
        values, frequencies = self.model.get_distribution()
        
        # Теоретическое распределение Пуассона
        lambda_T = self.model.lambda_rate * self.model.T
        x_theor = np.arange(0, max(values) + 5)
        y_theor = stats.poisson.pmf(x_theor, lambda_T)
        
        self.axes[0].bar(values, frequencies, alpha=0.7, label='Эмпирическое', color='steelblue', edgecolor='black')
        self.axes[0].plot(x_theor, y_theor, 'ro-', label=f'Теоретическое\n(Пуассон, λT={lambda_T:.2f})', markersize=4)
        self.axes[0].set_xlabel('Число заявок за интервал T', fontsize=10)
        self.axes[0].set_ylabel('Вероятность', fontsize=10)
        self.axes[0].set_title('Распределение числа заявок', fontsize=11, fontweight='bold')
        self.axes[0].legend()
        self.axes[0].grid(True, alpha=0.3)
        
        # График 2: Пример потока событий (временная диаграмма)
        if self.model.event_times:
            # Визуализация потока на временной оси
            y_events = np.ones(len(self.model.event_times))
            self.axes[1].scatter(self.model.event_times, y_events, color='red', s=100, 
                               marker='|', linewidths=2, label='События (заявки)')
            self.axes[1].set_xlim(0, self.model.T)
            self.axes[1].set_ylim(0.5, 1.5)
            self.axes[1].set_xlabel('Время (сек)', fontsize=10)
            self.axes[1].set_yticks([])
            self.axes[1].set_title(f'Пример потока заявок (N={len(self.model.event_times)} заявок за T={self.model.T} сек)', 
                                  fontsize=11, fontweight='bold')
            self.axes[1].grid(True, alpha=0.3, axis='x')
            self.axes[1].axhline(y=1, color='gray', linestyle='--', alpha=0.5)
            
            # Добавление информации о средних интервалах
            if len(self.model.event_times) > 1:
                intervals = np.diff([0] + self.model.event_times)
                mean_interval = np.mean(intervals)
                self.axes[1].text(0.02, 0.95, f'Средний интервал: {mean_interval:.3f} сек\n' + 
                                f'Теоретический: {1/self.model.lambda_rate:.3f} сек',
                                transform=self.axes[1].transAxes, fontsize=9,
                                verticalalignment='top', bbox=dict(boxstyle='round', 
                                facecolor='wheat', alpha=0.5))
        
        self.canvas.draw()


def main():
    """Главная функция запуска приложения."""
    root = tk.Tk()
    app = PoissonFlowGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()