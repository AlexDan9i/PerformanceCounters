import psutil
import time
import csv
from datetime import datetime

# Имя файла для сохранения данных
output_file = "performance_data.csv"

def write_header():
    """Создает файл и записывает заголовки столбцов"""
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow([
            "Timestamp",
            "PID",
            "Process Name",
            "CPU Usage (%)",
            "Memory Usage (MB)",
            "Disk Read (MB)",
            "Disk Write (MB)",
        ])

def initialize_cpu_percent():
    """Инициализирует значения CPU для всех процессов"""
    for proc in psutil.process_iter(['pid']):
        try:
            proc.cpu_percent(interval=None)  # Инициализация CPU данных
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

def log_performance_data():
    """Собирает данные о процессах и записывает их в файл"""
    with open(output_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=';')

        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'io_counters']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                cpu_usage = proc.cpu_percent(interval=0.1)  # Замер CPU с небольшим интервалом
                memory_usage = proc.info['memory_info'].rss / (1024 * 1024)  # Преобразование в MB
                io_counters = proc.info['io_counters']
                disk_read = io_counters.read_bytes / (1024 * 1024) if io_counters else 0
                disk_write = io_counters.write_bytes / (1024 * 1024) if io_counters else 0

                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    pid,
                    name,
                    cpu_usage,
                    memory_usage,
                    disk_read,
                    disk_write
                ])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

def get_top_processes():
    """Возвращает топ-10 процессов по загрузке CPU"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            processes.append((proc.info['pid'], proc.info['name'], proc.cpu_percent(interval=0.1)))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    top_processes = sorted(processes, key=lambda x: x[2], reverse=True)[:10]
    print("\nТоп-10 процессов по загрузке CPU:")
    for pid, name, cpu in top_processes:
        print(f"PID: {pid}, Name: {name}, CPU Usage: {cpu}%")

if __name__ == "__main__":
    write_header()
    initialize_cpu_percent()  # Инициализация CPU данных
    print("Сбор данных начался. Нажмите Ctrl+C для завершения.")
    try:
        while True:
            log_performance_data()
            time.sleep(5)  # Интервал сбора данных (в секундах)
            get_top_processes()
    except KeyboardInterrupt:
        print("Сбор данных завершен.")
