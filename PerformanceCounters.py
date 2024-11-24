import psutil
import time
import csv
from datetime import datetime


output_file = "performance_data.csv"
top_processes_file = "top_processes_data.csv"

# Имя файла для сохранения данных
def write_headers():
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
            "Network Sent (MB)",
            "Network Received (MB)"
        ])
    with open(top_processes_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow([
            "Timestamp",
            "PID",
            "Process Name",
            "CPU Usage (%)",
            "Memory Usage (MB)",
            "Disk Read (MB)",
            "Disk Write (MB)",
            "Network Sent (MB)",
            "Network Received (MB)"
        ])    
# Получаем количество логических ядер
cpu_count = psutil.cpu_count()
# Даем системе немного времени для измерения CPU загрузки
time.sleep(1)

# Получаем данные по каждому процессу
def log_data():
   """Собирает данные о процессах и записывает их в файл"""
   with open(output_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=';')       
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'io_counters']):
            try:
                 pid = proc.info['pid']
                 name = proc.info['name']
                 cpu_percent = round(proc.info['cpu_percent'] / cpu_count, 2)  # Нормализуем по количеству ядер
                 memory_usage = round(proc.info['memory_info'].rss / (1024 * 1024), 2)  # Преобразование в MB
                 io_counters = proc.info['io_counters']
                 disk_read = round(io_counters.read_bytes / (1024 * 1024), 2) if io_counters else 0
                 disk_write = round(io_counters.write_bytes / (1024 * 1024), 2) if io_counters else 0
                 net_io = psutil.net_io_counters(pernic=False)
                 net_sent = round(net_io.bytes_sent / (1024 * 1024), 2)
                 net_recv = round(net_io.bytes_recv / (1024 * 1024), 2)
        
                 writer.writerow([
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     pid,
                     name,
                     cpu_percent,
                     memory_usage,
                     disk_read,
                     disk_write,
                     net_sent,
                     net_recv
                ])
        #print(f"PID: {pid}, Process Name: {name}, CPU Usage (на ядро): {cpu_percent:.2f}%")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
               continue

def log_top_processes():
    """Собирает данные о топ-10 процессах по CPU и записывает их в файл"""
    with open(top_processes_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=';')

        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'io_counters']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                cpu_usage = round(proc.info['cpu_percent'] / cpu_count, 2)
                memory_usage = round(proc.info['memory_info'].rss / (1024 * 1024), 2)  # MB

                io_counters = proc.info['io_counters']
                disk_read = round(io_counters.read_bytes / (1024 * 1024), 2) if io_counters else 0
                disk_write = round(io_counters.write_bytes / (1024 * 1024), 2) if io_counters else 0

                net_io = psutil.net_io_counters(pernic=False)
                net_sent = round(net_io.bytes_sent / (1024 * 1024), 2)
                net_recv = round(net_io.bytes_recv / (1024 * 1024),2)

                processes.append((
                    pid,
                    name,
                    cpu_usage,
                    memory_usage,
                    disk_read,
                    disk_write,
                    net_sent,
                    net_recv
                ))

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue  

        top_processes = sorted(processes, key=lambda x: x[2], reverse=True)[:10]

        for proc_data in top_processes:
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                *proc_data
            ])
              

if __name__ == "__main__":
       write_headers()
       print("Сбор данных начался. Нажмите Ctrl+C для завершения.")
       try:
           while True:
              log_data()
              log_top_processes()
              time.sleep(5)  # Интервал сбора данных (в секундах)
       except KeyboardInterrupt:
              print("Сбор данных завершен.")