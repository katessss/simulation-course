# Отчёт по лабораторной: Моделирование полёта тела в атмосфере

**Задание:**  
Реализовать приложение для моделирования полёта тела в атмосфере.  
Предусмотреть возможность ввода шага моделирования и вывода результатов.
Выполнить моделирование **без очистки предыдущих результатов** для различных шагов моделирования, сравнить траектории и заполнить таблицу.
Сделать выводы.

---

### Код программы:
Импорт библиотек и константы:

    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import tkinter as tk
    from tkinter import ttk, messagebox

    G = 9.81 
    RHO = 1.225  
    C = 0.15 

### Вычисление ускорения
<img width="779" height="423" alt="Снимок экрана 2026-02-18 161118" src="https://github.com/user-attachments/assets/04bf7bd0-30c8-481b-a45c-c7269e578bb5" />

    # Вычисляет производные: [dx/dt, dy/dt, dvx/dt, dvy/dt]
    def get_derivatives(state, m, S):
        x, y, vx, vy = state
        v = np.sqrt(vx**2 + vy**2) # модуль вектора скорости
        k = C * RHO * S / (2*m) # Баллистический коэффициент

        # ускорения
        ax = -k * vx * v
        ay = -G - k * vy * v
        return np.array([vx, vy, ax, ay])


### Один шаг полёта
<img width="779" height="423" alt="image" src="https://github.com/user-attachments/assets/90f7468c-11f7-46f0-a29b-dcc084e88cbf" />

    def step_RungeKutta_4(state, dt, m, S):
        k1 = get_derivatives(state, m, S)
        k2 = get_derivatives(state + k1 * dt / 2, m, S)
        k3 = get_derivatives(state + k2 * dt / 2, m, S)
        k4 = get_derivatives(state + k3 * dt, m, S)
        
        new_state = state + (k1 + 2*k2 + 2*k3 + k4) * dt / 6 # где мы?
        return new_state


### Симуляция полёта
    def simulate(v0, angle, dt, m, S):
        # начальные условия
        angle_rad = np.radians(angle)
        vx = v0 * np.cos(angle_rad)
        vy = v0 * np.sin(angle_rad)
        
        # [x, y, vx, vy]
        state = np.array([0.0, 0.0, vx, vy])
        
        # инфа о пути
        traj_x, traj_y = [0.0], [0.0]
        max_h = 0.0

        while state[1] >= 0: # пока не упало
            state = step_RungeKutta_4(state, dt, m, S)
            if state[1] >= 0:
                traj_x.append(state[0])
                traj_y.append(state[1])
                max_h = max(max_h, state[1])

        final_v = np.sqrt(state[2]**2 + state[3]**2)
        return traj_x, traj_y, state[0], max_h, final_v

### Визуализация
    def add_to_table(dt, dist, height, velocity):
        table.insert('', tk.END, values=(
            f"{dt}",
            f"{dist:.2f}",
            f"{height:.2f}",
            f"{velocity:.2f}"
        ))


    # Рисует новую траекторию на графике
    def update_plot(x, y, label):
        ax.plot(x, y, linewidth=2, label=label)
        ax.legend()
        ax.relim()
        ax.autoscale_view()
        canvas.draw()

    # Запустить
    def on_run_manual():
        try:
            v0 = float(v0_entry.get())
            angle = float(angle_entry.get())
            dt = float(dt_entry.get())
            m = float(m_entry.get())
            S = float(s_entry.get())

            x_list, y_list, dist, h_max, v_end = simulate(v0, angle, dt, m, S)
            
            update_plot(x_list, y_list, f"dt={dt}")
            add_to_table(dt, dist, h_max, v_end)
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числовые значения")

    # Выполнить задание
    def on_auto_fill():
        try:
            v0 = float(v0_entry.get())
            angle = float(angle_entry.get())
            m = float(m_entry.get())
            S = float(s_entry.get())

            steps = [1, 0.1, 0.01, 0.001, 0.0001]
            
            for dt in steps:
                x_list, y_list, dist, h_max, v_end = simulate(v0, angle, dt, m, S)
                update_plot(x_list, y_list, f"dt={dt}")
                add_to_table(dt, dist, h_max, v_end)
                
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте параметры ввода (v0, угол, m, S)")

    # Очистка
    def on_clear():
        ax.clear()
        ax.set_xlabel('Дальность (м)')
        ax.set_ylabel('Высота (м)')
        ax.set_title('Траектории полёта')
        ax.grid(True, alpha=0.3)
        canvas.draw()
        
        for item in table.get_children():
            table.delete(item)



    root = tk.Tk()
    root.title("Моделирование полета (Процедурный стиль)")
    root.geometry("1100x700")

    # Левая панель управления
    ctrl_frame = ttk.Frame(root, padding=10)
    ctrl_frame.pack(side=tk.RIGHT, fill=tk.Y)

    # Поля ввода
    inputs = [
        ("Начальная скорость (м/с):", "1", "v0"),
        ("Угол запуска (град):", "10", "angle"),
        ("Шаг моделирования (с):", "0.01", "dt"),
        ("Масса (кг):", "1.0", "m"),
        ("Площадь (м²):", "0.01", "S")
    ]

    entries = {}
    for i, (label_text, default, key) in enumerate(inputs):
        ttk.Label(ctrl_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=2)
        entry = ttk.Entry(ctrl_frame, width=15)
        entry.insert(0, default)
        entry.grid(row=i, column=1, pady=2)
        entries[key] = entry

    # Упрощаем доступ к Entry
    v0_entry = entries['v0']
    angle_entry = entries['angle']
    dt_entry = entries['dt']
    m_entry = entries['m']
    s_entry = entries['S']

    # Кнопки
    ttk.Button(ctrl_frame, text="Запустить", command=on_run_manual).grid(row=5, column=0, columnspan=2, pady=10, sticky=tk.EW)
    ttk.Button(ctrl_frame, text="Выполнить задание", command=on_auto_fill).grid(row=6, column=0, columnspan=2, pady=5, sticky=tk.EW)
    ttk.Button(ctrl_frame, text="Очистить всё", command=on_clear).grid(row=7, column=0, columnspan=2, pady=5, sticky=tk.EW)

    # Таблица
    columns = ('dt', 'range', 'height', 'velocity')
    table = ttk.Treeview(ctrl_frame, columns=columns, show='headings', height=10)
    table.heading('dt', text='dt, с')
    table.heading('range', text='Дальность, м')
    table.heading('height', text='Высота, м')
    table.heading('velocity', text='V кон, м/с')
    for col in columns:
        table.column(col, width=80, anchor=tk.CENTER)
    table.grid(row=8, column=0, columnspan=2, pady=10)

    # Область графика
    fig = Figure(figsize=(6, 5), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_xlabel('Дальность (м)')
    ax.set_ylabel('Высота (м)')
    ax.set_title('Траектории полёта')
    ax.grid(True, alpha=0.3)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    root.mainloop()

---


### Скриншот с несколькими траекториями:
<img width="853" height="785" alt="Снимок экрана 2026-02-18 165102" src="https://github.com/user-attachments/assets/29ae9ccb-45b0-47db-b165-27c85cfe7e1e" />


---

### Заполненная таблица:

|Шаг моделирования, с|1|0.1|0.01|0.001|0.0001|
|-|-|-|-|-|-|
| Дальность полёта, м | 253.53 | 247.28 | 246.34 | 246.31 | 246.30 |
| Максимальная высота, м | 73.93 | 74.00 | 74.01 | 74.01 | 74.01 |
| Скорость в конечной точке, м/с | 50.87 | 49.38 | 49.16 | 49.15 | 49.15 |

---

### Вывод:

В ходе выполнения лабораторной работы было проведено численное моделирование движения тела в атмосфере с использованием метода Рунге-Кутты 4-го порядка. Анализ полученных данных и графиков позволяет сделать следующие выводы:

* **Влияние шага на точность (Сходимость):**
   - При большом шаге ($dt = 1$ с) наблюдается значительная погрешность: расчетная дальность и конечная скорость заметно отклоняются от истинных значений. Это связано с тем, что физические силы сильно меняются в течение секунды, и грубый расчет не успевает их учесть.
   - Начиная с шага **$dt = 0.01$ с**, результаты стабилизируются. Разница в показателях между шагами $0.001$ и $0.0001$ практически отсутствует, что говорит о достижении сходимости решения.

* **Физическая адекватность модели:**
   - На графиках видно, что траектория не является идеальной параболой. Под действием сопротивления воздуха она превращается в баллистическую кривую: тело падает под более крутым углом, чем взлетало, а его конечная скорость меньше начальной из-за потерии энергии.

Применение метода **Рунге-Кутты 4-го порядка** позволило получить высокую точность даже на средних шагах моделирования, данный алгоритм сохраняет стабильность траектории при изменении шага интегрирования.






