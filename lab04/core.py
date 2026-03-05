import time


class SimpleCustomHash:    
    def _rotate_left(value, shift):        
        return ((value << shift) & 0xFFFFFFFF) | (value >> (32 - shift)) # циклический сдвиг влево 

    def custom_hash(data_bytes):
        h = 0x6a09e667 
        
        for byte in data_bytes:
            h ^= byte
            h = (h + 0x9e3779b9) & 0xFFFFFFFF 
            h = SimpleCustomHash._rotate_left(h, 13)
            h ^= (h >> 16)
        
        return h



class CSPRNG_Manual:
    def __init__(self, seed=None):
        seed_str = str(seed or time.time()).encode()
        self.key = SimpleCustomHash.custom_hash(seed_str)
        self.counter = 0

    def next_bits(self):
        self.counter += 1
        # Конкатенируем ключ и счетчик, хешируем
        counter_bytes = self.counter.to_bytes(8, 'big') #
        key_bytes = self.key.to_bytes(4, 'big') 
        data = key_bytes + counter_bytes # Склеиваем байты и хешируем
        return SimpleCustomHash.custom_hash(data)

    def get_uniform(self): # Возвращаем число в диапазоне [0, 1)
        bits = self.next_bits()
        return bits / 0xFFFFFFFF
