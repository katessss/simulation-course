import tkinter as tk
from tkinter import ttk, messagebox
import time
import random
import math

class SimpleCustomHash:   
    @staticmethod 
    def _rotate_left(value, shift):        
        return ((value << shift) & 0xFFFFFFFF) | (value >> (32 - shift)) # циклический сдвиг влево 

    @staticmethod 
    def custom_hash(data_bytes):
        h = 0x6a09e667 # стартовый вектор
        
        for byte in data_bytes:
            h ^= byte
            h = (h + 0x9e3779b9) & 0xFFFFFFFF  # добавляет нелинейность
            h = SimpleCustomHash._rotate_left(h, 13)
            h ^= (h >> 16)
        
        return h



class CSPRNG_Manual:
    def __init__(self, seed=None):
        seed_str = str(seed or time.time()).encode()
        self.key = SimpleCustomHash.custom_hash(seed_str)
        self.counter = 0

    def next_val(self):
        self.counter += 1
        # Конкатенируем ключ и счетчик, хешируем
        counter_bytes = self.counter.to_bytes(8, 'big') 
        key_bytes = self.key.to_bytes(4, 'big') 
        data = key_bytes + counter_bytes # Склеиваем байты и хешируем
        bits = SimpleCustomHash.custom_hash(data)
        return bits / 0xFFFFFFFF

        
class RNGAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализ датчиков случайных чисел")
        self.root.geometry("600x400")

        ttk.Label(root, text="Seed (оставьте пустым для авто):").pack(pady=(10, 0))
        self.seed_entry = ttk.Entry(root, width=30)
        self.seed_entry.pack(pady=5)

        ttk.Label(root, text="Размер выборки N:").pack(pady=(10, 0))
        self.n_entry = ttk.Entry(root, width=30)
        self.n_entry.insert(0, "100000")
        self.n_entry.pack(pady=5)

        self.run_btn = ttk.Button(root, text="Запустить расчет", command=self.run_analysis)
        self.run_btn.pack(pady=20)

        self.tree = ttk.Treeview(root, columns=("Metric", "Theory", "Manual", "BuiltIn"), show='headings', height=4)
        self.tree.heading("Metric", text="Параметр")
        self.tree.heading("Theory", text="Теория")
        self.tree.heading("Manual", text="CSPRNG (Свой)")
        self.tree.heading("BuiltIn", text="Встроенный")
        for col in ("Metric", "Theory", "Manual", "BuiltIn"):
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(padx=20, pady=10, fill="x")

    def calculate_stats(self, data):
        n = len(data)
        mean = sum(data) / n
        var = sum((x - mean)**2 for x in data) / n
        return mean, var

    def run_analysis(self):
        try:
            n = int(self.n_entry.get())
        except ValueError:
            messagebox.showerror("Ошибка", "N должно быть целым числом!")
            return

        seed_raw = self.seed_entry.get()
        seed = int(seed_raw) if seed_raw.strip() else int(time.time())

        man_gen = CSPRNG_Manual(seed)
        data_manual = [man_gen.next_val() for _ in range(n)]
        random.seed(seed)
        data_std = [random.random() for _ in range(n)]

        m1, v1 = self.calculate_stats(data_manual)
        m2, v2 = self.calculate_stats(data_std)

        for i in self.tree.get_children():
            self.tree.delete(i)
        
        self.tree.insert("", "end", values=("Среднее", "0.5000", f"{m1:.5f}", f"{m2:.5f}"))
        self.tree.insert("", "end", values=("Дисперсия", "0.0833", f"{v1:.5f}", f"{v2:.5f}"))

if __name__ == "__main__":
    root = tk.Tk()
    app = RNGAnalyzerApp(root)
    root.mainloop()