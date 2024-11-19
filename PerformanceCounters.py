import psutil
import csv
from datetime import datetime

# Function to collect performance data
def collect_data():
    # Get current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Initialize list for process data
    process_data = []

    # Collect data for all running processes
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            proc_info = proc.info
            process_data.append({
                'timestamp': timestamp,
                'process_name': proc_info['name'],
                'pid': proc_info['pid'],
                'cpu_percent': proc_info['cpu_percent'],
                'memory_usage_mb': proc_info['memory_info'].rss / (1024 * 1024),  # Convert to MB
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort by CPU usage and get top 30 processes
    top_processes = sorted(process_data, key=lambda x: x['cpu_percent'], reverse=True)[:30]

    # Collect overall system resource usage
    system_data = {
        'timestamp': timestamp,
        'cpu_usage_percent': psutil.cpu_percent(interval=1),
        'memory_usage_percent': psutil.virtual_memory().percent,
        'disk_usage_percent': psutil.disk_usage('/').percent,
        'network_sent_mb': psutil.net_io_counters().bytes_sent / (1024 * 1024),
        'network_recv_mb': psutil.net_io_counters().bytes_recv / (1024 * 1024),
    }

    return process_data, top_processes, system_data

# Write collected data to CSV files
def write_to_csv(process_data, top_processes, system_data):
    # File paths
    all_processes_file = 'all_processes.csv'
    top_processes_file = 'top_processes.csv'
    system_metrics_file = 'system_metrics.csv'

    # Write all processes data
    with open(all_processes_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['timestamp', 'process_name', 'pid', 'cpu_percent', 'memory_usage_mb'], delimiter=';')
        if file.tell() == 0:
            writer.writeheader()
        writer.writerows(process_data)

    # Write top processes data
    with open(top_processes_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['timestamp', 'process_name', 'pid', 'cpu_percent', 'memory_usage_mb'], delimiter=';')
        writer.writeheader()
        writer.writerows(top_processes)

    # Write system metrics data
    with open(system_metrics_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['timestamp', 'cpu_usage_percent', 'memory_usage_percent', 'disk_usage_percent', 'network_sent_mb', 'network_recv_mb'], delimiter=';')
        if file.tell() == 0:
            writer.writeheader()
        writer.writerow(system_data)

# Main execution loop
def main():
    try:
        while True:
            process_data, top_processes, system_data = collect_data()
            write_to_csv(process_data, top_processes, system_data)
            print(f"Data collected at {system_data['timestamp']}")
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")

if __name__ == "__main__":
    main()
