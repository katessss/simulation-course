

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


class WeatherMarkovEngine:

    def __init__(self, transition_matrix=None):

        if transition_matrix is None:
            # Матрица по умолчанию
            Q = [
            [-0.5,  0.3,  0.2],  # Из Ясно уходим со скоростью 0.5
            [ 0.4, -0.7,  0.3],  # Из Облачно уходим со скоростью 0.7
            [ 0.1,  0.4, -0.5]   # Из Пасмурно уходим со скоростью 0.5
        ]
        
        self.transition_matrix = np.array(Q, dtype=float)
        self.states = {1: 'Ясно', 2: 'Облачно', 3: 'Пасмурно'}
        self.current_state = 1
        self.history = []
        
        self._validate_matrix()
    
    def _validate_matrix(self):
        # Проверка размера
        if self.transition_matrix.shape != (3, 3):
            raise ValueError("Матрица переходов должна быть 3x3")
        
        # Проверка стохастичности (сумма строк = 1)
        row_sums = self.transition_matrix.sum(axis=1)
        if not np.allclose(row_sums, 0.0):
            raise ValueError("Сумма вероятностей в каждой строке должна быть равна 0")
        
    def set_transition_matrix(self, matrix):
        self.transition_matrix = np.array(matrix, dtype=float)
        self._validate_matrix()

    def reset(self, initial_state=1):
        self.current_state = initial_state
        self.history = []
   
    def get_transition_probability(self, from_state, to_state):
        return self.transition_matrix[from_state - 1, to_state - 1]
    
    
    # Делаем взвешенный случайный выбор
    def step(self):
        # Текущая интенсивность ухода (д    иагональный элемент с минусом)
        lambda_total = abs(self.transition_matrix[self.current_state - 1, self.current_state - 1])
        
        # duration = -ln(U) / lambda
        duration = random.expovariate(lambda_total) # генерация времени пребывания
        
        # Определяем, КУДА переходим
        # Вероятности переходов пропорциональны интенсивностям
        rates = self.transition_matrix[self.current_state - 1].copy()
        rates[self.current_state - 1] = 0  # Обнуляем диагональ
        probabilities = rates / lambda_total
        
        # Сохраняем длительность для истории
        self.history.append((self.current_state, duration))
        
        # Совершаем переход
        next_state = np.random.choice([1, 2, 3], p=probabilities)
        self.current_state = next_state
        
        return next_state, duration
    
    def get_stationary_distribution(self):
        Q = self.transition_matrix
        # Решаем систему уравнений π * Q = 0
        # Находим собственный вектор для собственного значения 0
        eigenvalues, eigenvectors = np.linalg.eig(Q.T) # (πQ)^T = Q^T * π^T 
        idx = np.argmin(np.abs(eigenvalues)) #находим индекс собственного числа, которое равно 0 (или очень близко к нему)
        stationary = np.real(eigenvectors[:, idx])  # берем соответствующий собственный вектор (отбрасываем мнимую часть, если есть)
        return stationary / stationary.sum()
    
    
    def get_empirical_distribution(self):
        total_time = sum(dur for state, dur in self.history)
        times = {1: 0, 2: 0, 3: 0}
        for state, dur in self.history:
            times[state] += dur
        return np.array([times[1]/total_time, times[2]/total_time, times[3]/total_time])
        
    
    def get_statistics(self):
        if not self.history:
            return None
        
        times = {1: 0.0, 2: 0.0, 3: 0.0}
        total_time = 0.0
        for state, dur in self.history:
            times[state] += dur
            total_time += dur
        
        empirical = self.get_empirical_distribution()
        stationary = self.get_stationary_distribution()
        
        return {
            'total_time': total_time,
            'total_events': len(self.history), # Добавили количество переходов
            'fractions': empirical,            # Добавили массив долей
            'stationary': stationary,          # Добавили массив теории
            # Остальные поля можно оставить для совместимости
            'sunny_fraction': empirical[0],
            'cloudy_fraction': empirical[1],
            'overcast_fraction': empirical[2],
            'stationary_sunny': stationary[0],
            'stationary_cloudy': stationary[1],
            'stationary_overcast': stationary[2]
        }
    
    def save_results(self, filename, n_days=None):
        # Создаем таблицу из истории кортежей
        df = pd.DataFrame(self.history, columns=['Состояние_код', 'Длительность'])
        df['Состояние_название'] = df['Состояние_код'].map(self.states)
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        # Статистика
        stats_filename = filename.replace('.csv', '_statistics.csv')
        stats = self.get_statistics()
        
        stat_df = pd.DataFrame({
            'Состояние': ['Ясно', 'Облачно', 'Пасмурно'],
            'Доля_времени': stats['fractions'],
            'Теоретическая_доля': stats['stationary']
        })
        stat_df.to_csv(stats_filename, index=False, encoding='utf-8-sig')
        
        return filename, stats_filename, ""

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
        if not self.history:
            return np.array([])
        
        cumulative = []
        running_times = {1: 0.0, 2: 0.0, 3: 0.0}
        current_total_time = 0.0
        
        for state, dur in self.history:
            running_times[state] += dur
            current_total_time += dur
            cumulative.append([
                running_times[1] / current_total_time,
                running_times[2] / current_total_time,
                running_times[3] / current_total_time
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
                             command=self.save_results, width=20)
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
        """Обновление всех графиков для непрерывного времени"""
        # Очистка всех осей
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        
        history = self.engine.history
        
        if len(history) == 0:
            self.canvas.draw()
            return
        
        # 1. Временной ряд (НЕПРЕРЫВНЫЙ)
        # Берем последние 50 переходов, чтобы график был читаемым
        display_history = history[-50:] if len(history) > 50 else history
        
        # Рассчитываем временную шкалу (ось X — это суммарное время)
        states = [h[0] for h in display_history]
        durations = [h[1] for h in display_history]
        
        # Точки времени: [0, d1, d1+d2, d1+d2+d3...]
        time_points = [0]
        for d in durations:
            time_points.append(time_points[-1] + d)
            
        # Рисуем ступенчатый график (состояние меняется в моменты времени)
        # where='post' означает, что состояние держится ДО следующей точки
        self.ax1.step(time_points[:-1], states, where='post', color='black', linewidth=1, zorder=3)
        
        # Раскрашиваем фон графика в цвета состояний
        for i in range(len(time_points)-1):
            self.ax1.axvspan(time_points[i], time_points[i+1], 
                             color=self.colors[states[i]], alpha=0.4)
        
        self.ax1.set_xlabel('Суммарное время', fontsize=9)
        self.ax1.set_ylabel('Состояние', fontsize=9)
        self.ax1.set_title(f'Непрерывный поток состояний (посл. {len(display_history)} событий)', fontsize=10)
        self.ax1.set_yticks([1, 2, 3])
        self.ax1.set_yticklabels(['Ясно', 'Облачно', 'Пасмурно'], fontsize=8)
        self.ax1.grid(axis='y', alpha=0.2)

        # 2. Сравнение распределений (ВРЕМЯ-ВЗВЕШЕННОЕ)
        # Здесь мы сравниваем долю ВРЕМЕНИ, проведенного в состоянии
        empirical = self.engine.get_empirical_distribution()
        stationary = self.engine.get_stationary_distribution()
        
        x = np.arange(3)
        width = 0.35
        
        self.ax2.bar(x - width/2, empirical, width, 
                    label='Эмпирич. (время)', color='skyblue', edgecolor='black')
        self.ax2.bar(x + width/2, stationary, width, 
                    label='Теоретич. (Q-стац)', color='lightcoral', edgecolor='black')
        
        self.ax2.set_xlabel('Состояние', fontsize=9)
        self.ax2.set_ylabel('Доля времени', fontsize=9)
        self.ax2.set_title('Распределение времени в состояниях', fontsize=10)
        self.ax2.set_xticks(x)
        self.ax2.set_xticklabels(['Ясно', 'Облачно', 'Пасмурно'], fontsize=8)
        self.ax2.legend(fontsize=7)
        self.ax2.set_ylim(0, 1)
        
        # Добавляем текстовые значения над столбцами
        for i, val in enumerate(empirical):
            self.ax2.text(i - width/2, val + 0.02, f'{val:.2f}', ha='center', fontsize=7)
        for i, val in enumerate(stationary):
            self.ax2.text(i + width/2, val + 0.02, f'{val:.2f}', ha='center', fontsize=7)

        # 3. Матрица интенсивностей Q (Heatmap)
        # Используем палитру 'coolwarm', так как диагональ отрицательная (холодная), 
        # а переходы положительные (теплые)
        im = self.ax3.imshow(self.engine.transition_matrix, cmap='coolwarm', 
                            aspect='auto')
        self.ax3.set_xticks([0, 1, 2])
        self.ax3.set_yticks([0, 1, 2])
        self.ax3.set_xticklabels(['Ясно', 'Облачно', 'Пасмурно'], fontsize=8)
        self.ax3.set_yticklabels(['Ясно', 'Облачно', 'Пасмурно'], fontsize=8)
        self.ax3.set_title('Матрица интенсивностей (Q)', fontsize=10)
        
        # Добавление значений интенсивностей в ячейки
        for i in range(3):
            for j in range(3):
                val = self.engine.transition_matrix[i, j]
                self.ax3.text(j, i, f'{val:.2f}',
                            ha="center", va="center", 
                            color="white" if abs(val) > 0.4 else "black", 
                            fontsize=9, fontweight='bold')

        # 4. Сходимость по времени (Кумулятивное распределение)
        if len(history) > 1:
            cumulative = self.engine.get_cumulative_distribution()
            # Ось X — это номер перехода (события)
            x_range = range(1, len(history) + 1)
            
            self.ax4.plot(x_range, cumulative[:, 0], label='Ясно', color=self.colors[1])
            self.ax4.plot(x_range, cumulative[:, 1], label='Облачно', color=self.colors[2])
            self.ax4.plot(x_range, cumulative[:, 2], label='Пасмурно', color=self.colors[3])
            
            # Теоретические линии (стационар)
            self.ax4.axhline(y=stationary[0], color=self.colors[1], linestyle='--', alpha=0.5)
            self.ax4.axhline(y=stationary[1], color=self.colors[2], linestyle='--', alpha=0.5)
            self.ax4.axhline(y=stationary[2], color=self.colors[3], linestyle='--', alpha=0.5)
            
            self.ax4.set_xlabel('Количество переходов', fontsize=9)
            self.ax4.set_ylabel('Доля накопленного времени', fontsize=9)
            self.ax4.set_title('Сходимость к Q-стационарному', fontsize=10)
            self.ax4.legend(fontsize=7, loc='best')
            self.ax4.grid(True, alpha=0.3)
            self.ax4.set_ylim(0, 1)
        
        self.figure.tight_layout(rect=[0, 0.03, 1, 0.96])
        self.canvas.draw()
    
    def _update_display(self):
        state = self.engine.current_state
        self.current_state_label.config(text=self.state_names[state], foreground=self.colors[state])
        
        stats = self.engine.get_statistics()
        if stats:
            # Меняем текст на "Дней"
            self.step_count_label.config(text=f"Прошло дней: {stats['total_time']:.2f}")
            
            txt = f"Всего переходов: {stats['total_events']}\n"
            txt += f"Общая длительность: {stats['total_time']:.2f} дн.\n\n"
            txt += "Распределение (в днях):\n"
            for i in range(1, 4):
                name = self.state_names[i]
                # Считаем реальное кол-во дней для каждого состояния
                actual_days = stats['fractions'][i-1] * stats['total_time']
                txt += f"{name:8}: {actual_days:5.2f} дн. ({stats['fractions'][i-1]*100:4.1f}%)\n"
        
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
        if self.is_running:
            next_state, duration = self.engine.step()
            self._update_display()
            
            # Длительность состояния умножаем на ползунок скорости
            delay = max(10, int(duration * self.animation_speed))
            self.root.after(delay, self._animation_loop)
        else:
            self.root.after(100, self._animation_loop)

            
    def save_results(self):
        """Сохранить результаты (исправленная версия)"""
        if not self.engine.history: # Добавили .engine
            messagebox.showwarning("Предупреждение", "Нет данных для сохранения.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv")],
            initialfile="weather_results.csv"
        )
        
        if not filename:
            return
        
        try:
            # 1. Создаем таблицу из истории, которая лежит в ENGINE
            df = pd.DataFrame(self.engine.history, columns=['Состояние_код', 'Длительность'])
            
            # 2. Мапим названия состояний (они тоже в ENGINE)
            df['Состояние_название'] = df['Состояние_код'].map(self.engine.states)
            
            # 3. Рассчитываем даты (если нужно, чтобы время было непрерывным)
            start_date = datetime.now()
            cumulative_days = 0.0
            dates = []
            for dur in df['Длительность']:
                dates.append((start_date + timedelta(days=cumulative_days)).strftime("%Y-%m-%d %H:%M:%S"))
                cumulative_days += dur
            df.insert(0, 'Дата_и_время', dates)
            
            # Сохраняем основной файл
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            # 4. Сохраняем статистику
            stats = self.engine.get_statistics()
            stats_filename = filename.replace('.csv', '_statistics.csv')
            stat_df = pd.DataFrame({
                'Состояние': ['Ясно', 'Облачно', 'Пасмурно'],
                'Доля_времени': stats['fractions'],
                'Теоретическая_доля': stats['stationary']
            })
            stat_df.to_csv(stats_filename, index=False, encoding='utf-8-sig')
            
            messagebox.showinfo("Успех", f"Результаты сохранены:\n{filename}\n{stats_filename}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении: {e}")

def main():
    root = tk.Tk()
    app = WeatherMarkovGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()