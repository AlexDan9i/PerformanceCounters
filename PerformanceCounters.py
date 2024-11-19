import psutil
import time

# Получаем количество логических ядер
cpu_count = psutil.cpu_count()

# Даем системе немного времени для измерения CPU загрузки
time.sleep(1)

# Получаем данные по каждому процессу
for proc in psutil.process_iter(attrs=["pid", "name", "cpu_percent"]):
    try:
        pid = proc.info['pid']
        name = proc.info['name']
        cpu_percent = proc.info['cpu_percent'] / cpu_count  # Нормализуем по количеству ядер
        print(f"PID: {pid}, Имя: {name}, Загрузка CPU (на ядро): {cpu_percent:.2f}%")
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        continue
