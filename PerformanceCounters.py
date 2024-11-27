import psutil
import json
import time
import os
import sys
import logging
from datetime import datetime, timezone
from collections import defaultdict

# Определяем директорию, где находится исполняемый файл
def get_base_directory():
    if getattr(sys, 'frozen', False):  # Если скрипт скомпилирован (frozen state)
        return os.path.dirname(sys.executable)
    else:  # Если запускается из исходного кода
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_directory()

# Изменяем пути файлов
system_info = os.path.join(BASE_DIR, "system_info.json")
top_processes_file = os.path.join(BASE_DIR, "top_processes_data.json")
top_processes_detailing_file = os.path.join(BASE_DIR, "top_processes_detailing_data.json")
error_log_file = os.path.join(BASE_DIR, "monitor_errors.log")

# Настройка логирования ошибок
logging.basicConfig(
    filename=error_log_file,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_error(message, exception=None):
    """
    Логирует сообщение об ошибке с необязательной детализацией исключения.
    """
    if exception:
        logging.error(f"{message}: {exception}")
    else:
        logging.error(message)

def save_to_json(data, filename):
    """
    Сохраняет данные в файл JSON. Если файл существует, добавляет данные к существующим.
    """
    try:
        if os.path.exists(filename):
            with open(filename, "r") as json_file:
                existing_data = json.load(json_file)
        else:
            existing_data = []
        existing_data.append(data)
        with open(filename, "w") as json_file:
            json.dump(existing_data, json_file, indent=4)
            #print(f"Данные успешно сохранены в {filename}")
    except Exception as e:
        log_error(f"Ошибка при сохранении данных в JSON {filename}", e)

def get_cpu_info():
    """
    Собирает информацию о процессоре, включая количество ядер, загрузку и статистику.
    """
    try:
        cpu_stats = psutil.cpu_stats()
        return {
            "timestamp": datetime.now().isoformat(),
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "processor_speed": psutil.cpu_freq().current if psutil.cpu_freq() else "Unknown",
            "ctx_switches": cpu_stats.ctx_switches,
            "interrupts": cpu_stats.interrupts,
            "soft_interrupts": cpu_stats.soft_interrupts,
            "syscalls": cpu_stats.syscalls,
            "cpu_usage_per_core": dict(enumerate(psutil.cpu_percent(percpu=True, interval=1))),
            "total_cpu_usage": psutil.cpu_percent(interval=1)
        }
    except Exception as e:
        log_error("Ошибка при получении информации о CPU", e)
        return {}

def get_memory_info():
    """
    Собирает информацию об оперативной памяти и swap-разделе.
    """
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "timestamp": datetime.now().isoformat(),
            "total_memory_Mb": mem.total / (1024.0 ** 2),
            "available_memory_Mb": mem.available / (1024.0 ** 2),
            "used_memory_Mb": mem.used / (1024.0 ** 2),
            "free_memory_Mb": mem.free / (1024.0 ** 2),
            "memory_percentage": mem.percent,
            "total_swap_Mb": swap.total / (1024.0 ** 2),
            "used_swap_Mb": swap.used / (1024.0 ** 2),
            "free_swap_Mb": swap.free / (1024.0 ** 2),
            "swap_sin_Mb": swap.sin / (1024.0 ** 2),
            "swap_sout_Mb": swap.sout / (1024.0 ** 2),
            "swap_percentage": swap.percent
        }
    except Exception as e:
        log_error("Ошибка при получении информации о памяти", e)
        return {}

def get_disk_io_counters():
    """
    Собирает информацию об использовании дисков, включая статистику ввода-вывода.
    """
    try:
        io_counters = psutil.disk_io_counters()
        partitions = psutil.disk_partitions()
        result = {"timestamp": datetime.now().isoformat(), "disk_usage": []}

        for p in partitions:
            try:
                if os.name == 'nt' and 'cdrom' in p.opts:
                    continue
                disk_usage = psutil.disk_usage(p.mountpoint)
                result["disk_usage"].append({
                    "mountpoint": p.mountpoint,
                    "usage_total_Mb": disk_usage.total / (1024.0 ** 2),
                    "partitions_used_Mb": disk_usage.used / (1024.0 ** 2),
                    "free_space_Mb": disk_usage.free / (1024.0 ** 2),
                    "disk_usage_percent": disk_usage.percent
                })
            except Exception as e:
                log_error(f"Ошибка при обработке раздела {p.mountpoint}", e)

        result.update({
            "read_count": io_counters.read_count,
            "write_count": io_counters.write_count,
            "read_bytes": io_counters.read_bytes,
            "write_bytes": io_counters.write_bytes,
            "read_time": io_counters.read_time,
            "write_time": io_counters.write_time
        })
        return result
    except Exception as e:
        log_error("Ошибка при получении информации о дисках", e)
        return {}

def monitor_network():
    """
    Собирает информацию о сетевых интерфейсах и их активности.
    """
    try:
        interval = 1
        prev_counters = psutil.net_io_counters(pernic=True)
        time.sleep(interval)
        curr_counters = psutil.net_io_counters(pernic=True)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        network_data = {"timestamp": timestamp, "interfaces": []}

        for nic, counters in curr_counters.items():
            prev = prev_counters.get(nic)
            if prev is not None:
                sent_kb = (counters.bytes_sent - prev.bytes_sent) / 1024
                recv_kb = (counters.bytes_recv - prev.bytes_recv) / 1024
                packets_sent = counters.packets_sent - prev.packets_sent
                packets_recv = counters.packets_recv - prev.packets_recv

                nic_info = psutil.net_if_addrs().get(nic, [])
                nic_status = psutil.net_if_stats().get(nic, None)
                nic_details = {
                    "interface": nic,
                    "bytes_sent_kb": round(sent_kb, 2),
                    "bytes_received_kb": round(recv_kb, 2),
                    "packets_sent": packets_sent,
                    "packets_received": packets_recv,
                    "addresses": [],
                    "is_up": nic_status.isup if nic_status else False,
                    "speed_mbps": nic_status.speed if nic_status else None,
                }

                for addr in nic_info:
                    address_data = {
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast,
                        "ptp": addr.ptp,
                    }
                    nic_details["addresses"].append(address_data)

                network_data["interfaces"].append(nic_details)

        return network_data
    except Exception as e:
        log_error("Ошибка при мониторинге сети", e)
        return {}

def get_top_10_resource_intensive_processes():
    process_aggregation = defaultdict(lambda: {
        "cpu_percent": 0,
        "memory_percent": 0,
        "memory_info_rss_Mb": 0,
        "memory_info_vms_Mb": 0,
        "num_processes": 0,
        "exe": None,
        "name": None
    })

    # Общее количество логических ядер
    total_logical_cores = psutil.cpu_count(logical=True)

    # Фиксация времени запуска функции
    timestamp = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'memory_info', 'memory_percent', 'exe']):
        try:
            # Получаем информацию о процессе
            proc_info = proc.info
            exe_path = proc_info.get('exe') or proc_info.get('name')  # Используем путь к исполняемому файлу или имя
            if not exe_path:
                continue
            
            # Агрегируем данные
            process_aggregation[exe_path]["cpu_percent"] += proc_info.get('cpu_percent', 0) / total_logical_cores  # Нормируем на количество логических ядер
            process_aggregation[exe_path]["memory_percent"] += proc_info.get('memory_percent', 0)

            memory_info = proc_info.get('memory_info')
            if memory_info:
                process_aggregation[exe_path]["memory_info_rss_Mb"] += memory_info.rss / (1024 ** 2)  # RAM usage in MB
                process_aggregation[exe_path]["memory_info_vms_Mb"] += memory_info.vms / (1024 ** 2)  # Virtual memory in MB
            
            process_aggregation[exe_path]["num_processes"] += 1
            process_aggregation[exe_path]["exe"] = exe_path
            process_aggregation[exe_path]["name"] = proc_info.get('name', 'Unknown')
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Преобразуем агрегированные данные в список
    aggregated_processes = [
        {
            "name": data["name"],
            "exe": data["exe"],
            "cpu_percent": data["cpu_percent"],
            "memory_percent": data["memory_percent"],
            "memory_info_rss_Mb": data["memory_info_rss_Mb"],
            "memory_info_vms_Mb": data["memory_info_vms_Mb"],
            "num_processes": data["num_processes"]
        }
        for data in process_aggregation.values()
    ]

    # Сортируем по CPU и памяти
    sorted_aggregated_processes = sorted(
        aggregated_processes,
        key=lambda x: (x["cpu_percent"], x["memory_percent"]),
        reverse=True
    )

    # Возвращаем топ-10 приложений
    top_10_aggregated_processes = sorted_aggregated_processes[:10]
    return {"timestamp": timestamp, "processes": top_10_aggregated_processes}

def get_top_10_resource_intensive_processes_detailing():

    process_info = []

     # Фиксация времени запуска функции
    timestamp = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'memory_info', 'memory_percent', 'status', 'cpu_times', 'create_time', 'exe', 'cmdline', 'username', 'num_threads', 'ppid']):
        try:
            proc_info = proc.info

            # Память
            memory_info = proc_info.get('memory_info')
            memory_info_dict = {
                "rss_Mb": memory_info.rss / (1024 ** 2) if memory_info else 0,  # RAM usage in MB
                "vms_Mb": memory_info.vms / (1024 ** 2) if memory_info else 0   # Virtual memory in MB
            }

            # Время CPU
            cpu_times = proc_info.get('cpu_times')
            cpu_times_dict = {
                "user": cpu_times.user if cpu_times else 0,  
                "system": cpu_times.system if cpu_times else 0,
                "child_user": getattr(cpu_times, 'children_user', 0),  
                "child_system": getattr(cpu_times, 'children_system', 0)  
            }

            create_time = proc_info.get('create_time')
            readable_create_time = (
                datetime.fromtimestamp(create_time, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S') 
                if create_time else "Unknown"
            )

            # IO
            io_counters = proc.as_dict(attrs=['io_counters']).get('io_counters', None)
            io_counters_dict = {
                "read_count": io_counters.read_count if io_counters else 0,  
                "write_count": io_counters.write_count if io_counters else 0,  
                "read_bytes_Mb": io_counters.read_bytes / (1024 ** 2) if io_counters else 0,  
                "write_bytes_Mb": io_counters.write_bytes / (1024 ** 2) if io_counters else 0,  
                #"read_time": io_counters.read_time if io_counters else 0,  
                #"write_time": io_counters.write_time if io_counters else 0  
            }

            # Обновляем информацию о процессе
            proc_info['memory_info'] = memory_info_dict
            proc_info['cpu_times'] = cpu_times_dict
            proc_info['io_counters'] = io_counters_dict
            proc_info['create_time'] = readable_create_time

            process_info.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Сортируем по CPU и использованию памяти
    sorted_processes = sorted(
        process_info,
        key=lambda x: (x.get('cpu_percent', 0), x.get('memory_percent', 0)),
        reverse=True
    )

    # Возвращаем топ-10 процессов
    top_10_processes = sorted_processes[:10]
    return {"timestamp": timestamp, "processes": top_10_processes}

# Запуск скрипта 
if __name__ == "__main__":
    try:
        print("=" * 40)
        print("System Monitoring")
        print("=" * 40)
        print("Сбор данных начался. Нажмите Ctrl+C для завершения.")

        while True:
            data = {
                "cpu_info": get_cpu_info(),
                "memory_info": get_memory_info(),
                "disk_io_counters": get_disk_io_counters(),
                "network_data": monitor_network()
            }
            top_processes = get_top_10_resource_intensive_processes()
            top_processes_detailing = get_top_10_resource_intensive_processes_detailing()
            save_to_json(data, system_info)
            save_to_json(top_processes, top_processes_file)
            save_to_json(top_processes_detailing, top_processes_detailing_file)
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nМониторинг завершён.")
   
