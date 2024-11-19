import psutil
import time
import csv
from datetime import datetime

# Файлы для сохранения данных
output_file = "performance_data.csv"
top_processes_file = "top_processes.csv"


def write_headers():
    """Создает файлы и записывает заголовки столбцов"""
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Timestamp",
            "Host IP",
            "Subnet Mask",
            "Gateway IP"
        ])

    with open(top_processes_file, mode="w", newline="", encoding="utf-8") as file:
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
    """Собирает данные о локальной сети и записывает их в файл"""
    with open(output_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()

            for iface, addrs_list in addrs.items():
                for addr in addrs_list:
                    if addr.family == psutil.AF_INET:  # IPv4
                        writer.writerow([
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            addr.address,
                            addr.netmask,
                            stats[iface].isup
                        ])

        except Exception as e:
            print(f"Ошибка при сборе данных о сети: {e}")


def log_top_processes():
    """Собирает данные о топ-10 процессах по CPU и записывает их в файл"""
    with open(top_processes_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'io_counters']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                cpu_usage = proc.info['cpu_percent']
                memory_usage = proc.info['memory_info'].rss / (1024 * 1024)  # MB

                io_counters = proc.info['io_counters']
                disk_read = io_counters.read_bytes / (1024 * 1024) if io_counters else 0
                disk_write = io_counters.write_bytes / (1024 * 1024) if io_counters else 0

                net_io = psutil.net_io_counters(pernic=False)
                net_sent = net_io.bytes_sent / (1024 * 1024)
                net_recv = net_io.bytes_recv / (1024 * 1024)

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
            log_network_data()
            log_top_processes()
            time.sleep(5)  # Интервал сбора данных в секундах
    except KeyboardInterrupt:
        print("Сбор данных завершен.")
