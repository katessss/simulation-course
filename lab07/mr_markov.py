

import numpy as np
from collections import Counter
import pandas as pd
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from collections import Counter
import random
from datetime import datetime


def moiseyev_generate(answers):
    A = random.random()
    for name, p_k in answers.items():
        A -= p_k
        if A <= 0:
            return name
    return answers[-1][0]

class WeatherMarkovEngine:

    def __init__(self, transition_matrix=None):

        if transition_matrix is None:
            # Матрица по умолчанию
            transition_matrix = [
                [0.7, 0.2, 0.1],
                [0.3, 0.4, 0.3],
                [0.2, 0.3, 0.5]
            ]
        
        self.transition_matrix = np.array(transition_matrix, dtype=float)
        self.states = {1: 'Ясно', 2: 'Облачно', 3: 'Пасмурно'}
        self.current_state = 1
        self.history = []
        self.step_count = 0
        
        self._validate_matrix()
    
    def _validate_matrix(self):
        # Проверка размера
        if self.transition_matrix.shape != (3, 3):
            raise ValueError("Матрица переходов должна быть 3x3")
        
        # Проверка стохастичности (сумма строк = 1)
        row_sums = self.transition_matrix.sum(axis=1)
        if not np.allclose(row_sums, 1.0):
            raise ValueError("Сумма вероятностей в каждой строке должна быть равна 1")
        
        # Проверка неотрицательности
        if np.any(self.transition_matrix < 0):
            raise ValueError("Все вероятности должны быть неотрицательными")
    
    def set_transition_matrix(self, matrix):
        self.transition_matrix = np.array(matrix, dtype=float)
        self._validate_matrix()

    def reset(self, initial_state=1):

        self.current_state = initial_state
        self.history = [initial_state]
        self.step_count = 0
    
    def get_transition_probability(self, from_state, to_state):
        return self.transition_matrix[from_state - 1, to_state - 1]
    
    
    def get_stationary_distribution(self):
        # Решаем систему πP = π
        eigenvalues, eigenvectors = np.linalg.eig(self.transition_matrix.T) # (πP)^T = P^T * π^T 
        
        # Находим собственный вектор для собственного значения 1
        idx = np.argmin(np.abs(eigenvalues - 1)) #находим индекс собственного числа, которое равно 1 (или очень близко к нему)
        stationary = np.real(eigenvectors[:, idx])  # берем соответствующий собственный вектор (отбрасываем мнимую часть, если есть)
        stationary = stationary / stationary.sum() # норм
        
        return stationary
    
    # Делаем взвешенный случайный выбор
    def step(self):

        # Выбираем следующее состояние на основе текущего
        probabilities = self.transition_matrix[self.current_state - 1]

        answers = {i: p for i, p in enumerate(probabilities)}
        next_state = moiseyev_generate(answers) + 1

        # next_state = np.random.choice([1, 2, 3], p=probabilities)
                
        self.current_state = next_state
        self.history.append(next_state)
        self.step_count += 1
        
        return next_state
    
    
    def get_empirical_distribution(self):
        """
        Получить эмпирическое распределение из истории
        
        Returns:
            numpy array с частотами состояний [1, 2, 3]
        """
        if not self.history:
            return np.array([0.0, 0.0, 0.0])
        
        counter = Counter(self.history)
        total = len(self.history)
        
        return np.array([
            counter.get(1, 0) / total,
            counter.get(2, 0) / total,
            counter.get(3, 0) / total
        ])
    
    def get_statistics(self):
        """
        Получить статистику симуляции
        
        Returns:
            словарь со статистикой
        """
        if not self.history:
            return None
        
        counter = Counter(self.history)
        total_days = len(self.history)
        empirical = self.get_empirical_distribution()
        stationary = self.get_stationary_distribution()
        
        stats = {
            'total_days': total_days,
            'sunny_days': counter.get(1, 0),
            'cloudy_days': counter.get(2, 0),
            'overcast_days': counter.get(3, 0),
            'sunny_fraction': empirical[0],
            'cloudy_fraction': empirical[1],
            'overcast_fraction': empirical[2],
            'stationary_sunny': stationary[0],
            'stationary_cloudy': stationary[1],
            'stationary_overcast': stationary[2],
            'error_sunny': abs(empirical[0] - stationary[0]),
            'error_cloudy': abs(empirical[1] - stationary[1]),
            'error_overcast': abs(empirical[2] - stationary[2])
        }
        
        return stats
    
    def save_results(self, filename, n_days=None):
        """
        Сохранить результаты в CSV файлы
        
        Args:
            filename: базовое имя файла
            n_days: сохранить только последние n_days (None = все)
        """
        # Определяем диапазон для сохранения
        if n_days is None or n_days >= len(self.history):
            save_history = self.history
            start_day = 1
        else:
            save_history = self.history[-n_days:]
            start_day = len(self.history) - n_days + 1
        
        # 1. История симуляции
        dates = [datetime.now() + timedelta(days=i) for i in range(len(save_history))]
        
        df = pd.DataFrame({
            'День': range(start_day, start_day + len(save_history)),
            'Дата': dates,
            'Состояние_код': save_history,
            'Состояние_название': [self.states[s] for s in save_history]
        })
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        # 2. Статистика
        stats_filename = filename.replace('.csv', '_statistics.csv')
        
        counter = Counter(save_history)
        empirical_dist = pd.DataFrame({
            'Состояние': ['Ясно', 'Облачно', 'Пасмурно'],
            'Код': [1, 2, 3],
            'Количество_дней': [counter.get(i, 0) for i in [1, 2, 3]],
            'Эмпирическая_вероятность': [counter.get(i, 0) / len(save_history) for i in [1, 2, 3]]
        })
        
        stationary = self.get_stationary_distribution()
        empirical_dist['Теоретическая_вероятность'] = stationary
        empirical_dist['Разница'] = abs(empirical_dist['Эмпирическая_вероятность'] - 
                                        empirical_dist['Теоретическая_вероятность'])
        
        empirical_dist.to_csv(stats_filename, index=False, encoding='utf-8-sig')
        
        # 3. Матрица переходов
        matrix_filename = filename.replace('.csv', '_transition_matrix.csv')
        transition_df = pd.DataFrame(
            self.transition_matrix,
            columns=['Ясно', 'Облачно', 'Пасмурно'],
            index=['Ясно', 'Облачно', 'Пасмурно']
        )
        transition_df.to_csv(matrix_filename, encoding='utf-8-sig')
        
        return filename, stats_filename, matrix_filename
    
    def get_history_slice(self, start=None, end=None):
        """
        Получить срез истории
        
        Args:
            start: начальный индекс
            end: конечный индекс
            
        Returns:
            список состояний
        """
        return self.history[start:end]
    
    def get_cumulative_distribution(self):
        """
        Получить кумулятивное распределение по дням
        
        Returns:
            numpy array размера (len(history), 3) с вероятностями по дням
        """
        if not self.history:
            return np.array([])
        
        cumulative = []
        for i in range(1, len(self.history) + 1):
            counter = Counter(self.history[:i])
            cumulative.append([
                counter.get(1, 0) / i,
                counter.get(2, 0) / i,
                counter.get(3, 0) / i
            ])
        
        return np.array(cumulative)
    


class WeatherMarkovGUI:
    """
    Графический интерфейс для марковской модели погоды
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Марковская модель погоды")
        self.root.geometry("1400x900")
        
        # Инициализация движка модели
        self.engine = WeatherMarkovEngine()
        
        # Флаги управления
        self.is_running = False
        self.animation_speed = 100  # мс между шагами
        
        # Цвета для состояний
        self.colors = {1: '#FFD700', 2: '#B0C4DE', 3: '#708090'}
        self.state_names = {1: 'Ясно', 2: 'Облачно', 3: 'Пасмурно'}
        
        # Создание UI
        self._create_widgets()
        self._setup_plots()
        self._update_display()
        
        # Запуск главного цикла обновления
        self._animation_loop()
    
    def _create_widgets(self):
        """Создание виджетов интерфейса"""
        
        # ===== ЛЕВАЯ ПАНЕЛЬ: Управление =====
        left_frame = ttk.Frame(self.root, padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        # Заголовок
        title_label = ttk.Label(left_frame, text="Управление симуляцией", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # --- Матрица переходов ---
        matrix_label = ttk.Label(left_frame, text="Матрица переходов (интенсивности)", 
                                font=('Arial', 11, 'bold'))
        matrix_label.grid(row=1, column=0, columnspan=3, pady=(10, 5))
        
        # Заголовки столбцов
        ttk.Label(left_frame, text="→", font=('Arial', 9)).grid(row=2, column=0)
        ttk.Label(left_frame, text="Ясно", font=('Arial', 9, 'bold')).grid(row=2, column=1)
        ttk.Label(left_frame, text="Облачно", font=('Arial', 9, 'bold')).grid(row=2, column=2)
        ttk.Label(left_frame, text="Пасмурно", font=('Arial', 9, 'bold')).grid(row=2, column=3)
        
        # Создание полей ввода для матрицы
        self.matrix_entries = {}
        states = ['Ясно', 'Облачно', 'Пасмурно']
        
        for i, from_state in enumerate(states):
            # Заголовок строки
            ttk.Label(left_frame, text=from_state, font=('Arial', 9, 'bold')).grid(
                row=i+3, column=0, padx=5, sticky=tk.E)
            
            for j, to_state in enumerate(states):
                entry = ttk.Entry(left_frame, width=8, justify='center')
                entry.grid(row=i+3, column=j+1, padx=2, pady=2)
                
                # Получаем начальное значение из движка
                initial_value = self.engine.get_transition_probability(i+1, j+1)
                entry.insert(0, f"{initial_value:.2f}")
                
                self.matrix_entries[(i+1, j+1)] = entry
        
        # Кнопка применения матрицы
        apply_btn = ttk.Button(left_frame, text="Применить матрицу", 
                              command=self._apply_matrix)
        apply_btn.grid(row=6, column=0, columnspan=4, pady=10)
        
        # --- Текущее состояние ---
        ttk.Separator(left_frame, orient='horizontal').grid(
            row=7, column=0, columnspan=4, sticky='ew', pady=10)
        
        current_label = ttk.Label(left_frame, text="Текущее состояние", 
                                 font=('Arial', 11, 'bold'))
        current_label.grid(row=8, column=0, columnspan=4, pady=5)
        
        self.current_state_label = ttk.Label(left_frame, text="Ясно", 
                                            font=('Arial', 16, 'bold'),
                                            foreground='#FFD700')
        self.current_state_label.grid(row=9, column=0, columnspan=4, pady=5)
        
        self.step_count_label = ttk.Label(left_frame, text="День: 0", 
                                         font=('Arial', 10))
        self.step_count_label.grid(row=10, column=0, columnspan=4)
        
        # --- Управление симуляцией ---
        ttk.Separator(left_frame, orient='horizontal').grid(
            row=11, column=0, columnspan=4, sticky='ew', pady=10)
        
        control_label = ttk.Label(left_frame, text="Управление", 
                                 font=('Arial', 11, 'bold'))
        control_label.grid(row=12, column=0, columnspan=4, pady=5)
        
        # Кнопки управления
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=13, column=0, columnspan=4, pady=5)
        
        self.start_btn = ttk.Button(button_frame, text="▶ Старт", 
                                    command=self._start_simulation, width=15)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="⏸ Стоп", 
                                   command=self._stop_simulation, width=15,
                                   state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        self.reset_btn = ttk.Button(button_frame, text="🔄 Сброс", 
                                    command=self._reset_simulation, width=15)
        self.reset_btn.grid(row=1, column=0, padx=5, pady=5)
        
        self.step_btn = ttk.Button(button_frame, text="⏭ Шаг", 
                                   command=self._single_step, width=15)
        self.step_btn.grid(row=1, column=1, padx=5, pady=5)
        
        # Скорость анимации
        speed_label = ttk.Label(left_frame, text="Скорость (мс между шагами):", 
                               font=('Arial', 9))
        speed_label.grid(row=14, column=0, columnspan=4, pady=(10, 0))
        
        self.speed_var = tk.IntVar(value=100)
        speed_scale = ttk.Scale(left_frame, from_=10, to=1000, 
                               variable=self.speed_var, orient='horizontal',
                               command=self._update_speed)
        speed_scale.grid(row=15, column=0, columnspan=4, sticky='ew', padx=10)
        
        self.speed_label = ttk.Label(left_frame, text="100 мс", 
                                     font=('Arial', 9))
        self.speed_label.grid(row=16, column=0, columnspan=4)
        
        # --- Сохранение ---
        ttk.Separator(left_frame, orient='horizontal').grid(
            row=17, column=0, columnspan=4, sticky='ew', pady=10)
        
        save_label = ttk.Label(left_frame, text="Сохранение результатов", 
                              font=('Arial', 11, 'bold'))
        save_label.grid(row=18, column=0, columnspan=4, pady=5)
        
        days_frame = ttk.Frame(left_frame)
        days_frame.grid(row=19, column=0, columnspan=4, pady=5)
        
        ttk.Label(days_frame, text="Количество дней:").grid(row=0, column=0, padx=5)
        
        self.save_days_var = tk.StringVar(value="all")
        self.save_days_entry = ttk.Entry(days_frame, textvariable=self.save_days_var, 
                                        width=10, justify='center')
        self.save_days_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(days_frame, text="(all = все)").grid(row=0, column=2, padx=5)
        
        save_btn = ttk.Button(left_frame, text="💾 Сохранить в CSV", 
                             command=self._save_results, width=20)
        save_btn.grid(row=20, column=0, columnspan=4, pady=10)
        
        # --- Статистика ---
        ttk.Separator(left_frame, orient='horizontal').grid(
            row=21, column=0, columnspan=4, sticky='ew', pady=10)
        
        stats_label = ttk.Label(left_frame, text="Статистика", 
                               font=('Arial', 11, 'bold'))
        stats_label.grid(row=22, column=0, columnspan=4, pady=5)
        
        # Создаем текстовый виджет для статистики
        self.stats_text = tk.Text(left_frame, height=10, width=35, 
                                 font=('Courier', 9))
        self.stats_text.grid(row=23, column=0, columnspan=4, pady=5)
        
        # Настройка сетки
        left_frame.columnconfigure(1, weight=1)
        left_frame.columnconfigure(2, weight=1)
        left_frame.columnconfigure(3, weight=1)
        
        # ===== ПРАВАЯ ПАНЕЛЬ: Графики =====
        right_frame = ttk.Frame(self.root, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.W, tk.E))
        
        # Создание области для matplotlib
        self.figure = Figure(figsize=(10, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Настройка сетки главного окна
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def _setup_plots(self):
        """Настройка графиков"""
        self.figure.clear()
        
        # Создаем 4 subplot'а
        self.ax1 = self.figure.add_subplot(2, 2, 1)  # Временной ряд
        self.ax2 = self.figure.add_subplot(2, 2, 2)  # Сравнение распределений
        self.ax3 = self.figure.add_subplot(2, 2, 3)  # Матрица переходов
        self.ax4 = self.figure.add_subplot(2, 2, 4)  # Кумулятивное распределение
        
        self.figure.suptitle('Марковская модель погоды', fontsize=14, fontweight='bold')
        self.figure.tight_layout(rect=[0, 0.03, 1, 0.96])
    
    def _update_plots(self):
        """Обновление всех графиков"""
        # Очистка
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        
        history = self.engine.history
        
        if len(history) == 0:
            self.canvas.draw()
            return
        
        # 1. Временной ряд (показываем последние 100 точек)
        display_history = history[-100:] if len(history) > 100 else history
        start_idx = len(history) - len(display_history)
        days = list(range(start_idx + 1, start_idx + len(display_history) + 1))
        colors = [self.colors[state] for state in display_history]
        
        self.ax1.bar(days, display_history, color=colors, edgecolor='black', linewidth=0.5)
        self.ax1.set_xlabel('День', fontsize=9)
        self.ax1.set_ylabel('Состояние', fontsize=9)
        self.ax1.set_title(f'Временной ряд (последние {len(display_history)} дней)', fontsize=10)
        self.ax1.set_yticks([1, 2, 3])
        self.ax1.set_yticklabels(['Ясно', 'Облачно', 'Пасмурно'], fontsize=8)
        self.ax1.grid(axis='y', alpha=0.3)
        
        # 2. Сравнение распределений
        empirical = self.engine.get_empirical_distribution()
        stationary = self.engine.get_stationary_distribution()
        
        x = np.arange(3)
        width = 0.35
        
        bars1 = self.ax2.bar(x - width/2, empirical, width, 
                            label='Эмпирическое', color='skyblue', 
                            edgecolor='black', linewidth=1.5)
        bars2 = self.ax2.bar(x + width/2, stationary, width, 
                            label='Теоретическое', color='lightcoral', 
                            edgecolor='black', linewidth=1.5)
        
        self.ax2.set_xlabel('Состояние', fontsize=9)
        self.ax2.set_ylabel('Вероятность', fontsize=9)
        self.ax2.set_title('Сравнение распределений', fontsize=10)
        self.ax2.set_xticks(x)
        self.ax2.set_xticklabels(['Ясно', 'Облачно', 'Пасмурно'], fontsize=8)
        self.ax2.legend(fontsize=8)
        self.ax2.grid(axis='y', alpha=0.3)
        self.ax2.set_ylim(0, 1)
        
        # Добавление значений
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                self.ax2.text(bar.get_x() + bar.get_width()/2., height,
                            f'{height:.3f}', ha='center', va='bottom', fontsize=7)
        
        # 3. Матрица переходов (heatmap)
        im = self.ax3.imshow(self.engine.transition_matrix, cmap='YlOrRd', 
                            aspect='auto', vmin=0, vmax=1)
        self.ax3.set_xticks([0, 1, 2])
        self.ax3.set_yticks([0, 1, 2])
        self.ax3.set_xticklabels(['Ясно', 'Облачно', 'Пасмурно'], fontsize=8)
        self.ax3.set_yticklabels(['Ясно', 'Облачно', 'Пасмурно'], fontsize=8)
        self.ax3.set_xlabel('Следующее состояние', fontsize=9)
        self.ax3.set_ylabel('Текущее состояние', fontsize=9)
        self.ax3.set_title('Матрица переходов', fontsize=10)
        
        # Добавление значений в ячейки
        for i in range(3):
            for j in range(3):
                self.ax3.text(j, i, f'{self.engine.transition_matrix[i, j]:.2f}',
                            ha="center", va="center", color="black", 
                            fontsize=9, fontweight='bold')
        
        # 4. Кумулятивное распределение
        if len(history) > 1:
            cumulative = self.engine.get_cumulative_distribution()
            days_range = range(1, len(history) + 1)
            
            self.ax4.plot(days_range, cumulative[:, 0], 
                        label='Ясно', color=self.colors[1], linewidth=2)
            self.ax4.plot(days_range, cumulative[:, 1], 
                        label='Облачно', color=self.colors[2], linewidth=2)
            self.ax4.plot(days_range, cumulative[:, 2], 
                        label='Пасмурно', color=self.colors[3], linewidth=2)
            
            # Теоретические линии
            self.ax4.axhline(y=stationary[0], color=self.colors[1], 
                           linestyle='--', alpha=0.5)
            self.ax4.axhline(y=stationary[1], color=self.colors[2], 
                           linestyle='--', alpha=0.5)
            self.ax4.axhline(y=stationary[2], color=self.colors[3], 
                           linestyle='--', alpha=0.5)
            
            self.ax4.set_xlabel('День', fontsize=9)
            self.ax4.set_ylabel('Кумулятивная вероятность', fontsize=9)
            self.ax4.set_title('Сходимость к стационарному', fontsize=10)
            self.ax4.legend(fontsize=7, loc='best')
            self.ax4.grid(True, alpha=0.3)
            self.ax4.set_ylim(0, 1)
        
        self.figure.tight_layout(rect=[0, 0.03, 1, 0.96])
        self.canvas.draw()
    
    def _update_display(self):
        """Обновление отображаемой информации"""
        # Текущее состояние
        state = self.engine.current_state
        state_name = self.state_names[state]
        state_color = self.colors[state]
        
        self.current_state_label.config(text=state_name, foreground=state_color)
        self.step_count_label.config(text=f"День: {len(self.engine.history)}")
        
        # Статистика
        stats = self.engine.get_statistics()
        if stats:
            stationary = self.engine.get_stationary_distribution()
            
            stats_text = f"""
Общее количество дней: {stats['total_days']}

Эмпирическое распределение:
  Ясно:     {stats['sunny_days']:4d} ({stats['sunny_fraction']*100:5.2f}%)
  Облачно:  {stats['cloudy_days']:4d} ({stats['cloudy_fraction']*100:5.2f}%)
  Пасмурно: {stats['overcast_days']:4d} ({stats['overcast_fraction']*100:5.2f}%)

Теоретическое распределение:
  Ясно:     {stationary[0]*100:5.2f}%
  Облачно:  {stationary[1]*100:5.2f}%
  Пасмурно: {stationary[2]*100:5.2f}%

Разница (эмпир. - теорет.):
  Ясно:     {stats['error_sunny']*100:5.2f}%
  Облачно:  {stats['error_cloudy']*100:5.2f}%
  Пасмурно: {stats['error_overcast']*100:5.2f}%
            """
            
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
        
        # Обновление графиков
        self._update_plots()
    
    def _apply_matrix(self):
        """Применить матрицу переходов из полей ввода"""
        try:
            new_matrix = np.zeros((3, 3))
            
            for i in range(1, 4):
                for j in range(1, 4):
                    value = float(self.matrix_entries[(i, j)].get())
                    new_matrix[i-1, j-1] = value
                
            
            # Применение к движку
            self.engine.set_transition_matrix(new_matrix)
            
            # Обновление отображения
            self._update_display()
            
            messagebox.showinfo("Успех", "Матрица переходов обновлена и нормализована!")
            
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Некорректные значения в матрице:\n{e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка применения матрицы:\n{e}")
    
    def _start_simulation(self):
        """Запустить симуляцию"""
        self.is_running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
    
    def _stop_simulation(self):
        """Остановить симуляцию"""
        self.is_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
    
    def _reset_simulation(self):
        """Сбросить симуляцию"""
        self.is_running = False
        self.engine.reset(initial_state=1)
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self._update_display()
    
    def _single_step(self):
        """Выполнить один шаг"""
        self.engine.step()
        self._update_display()
    
    def _update_speed(self, value):
        """Обновить скорость анимации"""
        self.animation_speed = int(float(value))
        self.speed_label.config(text=f"{self.animation_speed} мс")
    
    def _animation_loop(self):
        """Главный цикл анимации"""
        if self.is_running:
            self.engine.step()
            self._update_display()
        
        # Планируем следующее обновление
        self.root.after(self.animation_speed, self._animation_loop)
    
    def _save_results(self):
        """Сохранить результаты"""
        if len(self.engine.history) == 0:
            messagebox.showwarning("Предупреждение", 
                                  "Нет данных для сохранения. Запустите симуляцию.")
            return
        
        # Получаем количество дней для сохранения
        days_str = self.save_days_var.get().strip().lower()
        
        if days_str == 'all' or days_str == '':
            n_days = None
            days_text = "все"
        else:
            try:
                n_days = int(days_str)
                if n_days <= 0:
                    messagebox.showerror("Ошибка", "Количество дней должно быть положительным")
                    return
                days_text = f"{n_days}"
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректное количество дней")
                return
        
        # Выбор файла для сохранения
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
            initialfile="weather_simulation_results.csv"
        )
        
        if not filename:
            return
        
        try:
            # Сохранение
            files = self.engine.save_results(filename, n_days=n_days)
            
            message = f"Сохранено {days_text} дней:\n\n"
            message += f"✓ {files[0]}\n"
            message += f"✓ {files[1]}\n"
            message += f"✓ {files[2]}"
            
            messagebox.showinfo("Успех", message)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения:\n{e}")


def main():
    root = tk.Tk()
    app = WeatherMarkovGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()