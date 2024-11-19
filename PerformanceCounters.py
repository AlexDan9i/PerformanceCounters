import psutil
import time
import csv
from datetime import datetime

# Имя файлов для сохранения данных
network_output_file = "network_data.csv"
top_processes_output_file = "top_processes_data.csv"

def write_network_header():
    """Создает файл и записывает заголовки для данных о сети"""
    with open(network_output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Timestamp",
            "Interface",
            "Bytes Sent (MB)",
            "Bytes Received (MB)",
            "Packets Sent",
            "Packets Received",
            "Errors Out",
            "Errors In"
        ])

def write_top_processes_header():
    """Создает файл и записывает заголовки для данных о процессах"""
    with open(top_processes_output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
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

def log_network_data():
    """Собирает данные о сети и записывает их в файл"""
    with open(network_output_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        net_io = psutil.net_io_counters(pernic=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for interface, stats in net_io.items():
            writer.writerow([
                timestamp,
                interface,
                stats.bytes_sent / (1024 * 1024),  # Преобразование в MB
                stats.bytes_recv / (1024 * 1024),  # Преобразование в MB
                stats.packets_sent,
                stats.packets_recv,
                stats.errout,
                stats.errin
            ])

def log_top_processes():
    """Собирает данные о топ-10 процессах и записывает их в файл"""
    with open(top_processes_output_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'io_counters']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                cpu_usage = proc.info['cpu_percent']
                memory_usage = proc.info['memory_info'].rss / (1024 * 1024)  # Преобразование в MB
                io_counters = proc.info['io_counters']
                disk_read = io_counters.read_bytes / (1024 * 1024) if io_counters else 0
                disk_write = io_counters.write_bytes / (1024 * 1024) if io_counters else 0

                # Собираем данные о сетевой активности для процесса
                net_counters = psutil.net_io_counters(pernic=False)
                net_sent = net_counters.bytes_sent / (1024 * 1024)
                net_recv = net_counters.bytes_recv / (1024 * 1024)

                processes.append((pid, name, cpu_usage, memory_usage, disk_read, disk_write, net_sent, net_recv))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Получаем топ-10 процессов по загрузке CPU
        top_processes = sorted(processes, key=lambda x: x[2], reverse=True)[:10]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for pid, name, cpu, memory, disk_read, disk_write, net_sent, net_recv in top_processes:
            writer.writerow([
                timestamp,
                pid,
                name,
                cpu,
                memory,
                disk_read,
                disk_write,
                net_sent,
                net_recv
            ])

def main():
    write_network_header()
    write_top_processes_header()

    print("Сбор данных начался. Нажмите Ctrl+C для завершения.")
    try:
        while True:
            log_network_data()
            log_top_processes()
            time.sleep(5)  # Интервал сбора данных (в секундах)
    except KeyboardInterrupt:
        print("Сбор данных завершен.")

if __name__ == "__main__":
    main()
