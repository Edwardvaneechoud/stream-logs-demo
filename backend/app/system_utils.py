# system_utils.py
import os
import psutil
from typing import Dict, Tuple, Any, Optional


def get_process_stats() -> Dict[str, Any]:
    """Get stats for the current process"""
    process = psutil.Process(os.getpid())
    return {
        "memory_info": process.memory_info(),
        "cpu_percent": process.cpu_percent(interval=0.5)
    }


def get_total_ram_usage() -> float:
    """Get the total RAM usage percentage"""
    return psutil.virtual_memory().percent


def get_ram_usage() -> Dict[str, str]:
    """Get RAM usage percentage for all processes"""
    total_ram = psutil.virtual_memory().total
    ram_usage_by_process = {}
    process_list = []

    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            pinfo = proc.info
            if pinfo and 'memory_info' in pinfo and pinfo['memory_info']:
                ram_percent = (pinfo['memory_info'].rss / total_ram) * 100
                process_list.append((pinfo['pid'], pinfo['name'], ram_percent))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Sort by RAM usage (descending) and get top 10
    process_list.sort(key=lambda x: x[2], reverse=True)
    top_processes = process_list[:10]

    # Format the result
    for pid, name, ram_percent in top_processes:
        ram_usage_by_process[f"{name} (PID: {pid})"] = f"{ram_percent:.2f}%"
    return ram_usage_by_process


def get_system_load() -> Tuple[float, Optional[float], Optional[float]]:
    """Get system load averages"""
    try:
        # Get 1, 5, and 15 minute load averages
        load1, load5, load15 = os.getloadavg()
        return load1, load5, load15
    except (AttributeError, OSError):
        # Fallback for systems without getloadavg (e.g., Windows)
        return psutil.cpu_percent(interval=0.1), None, None


def format_load_values(load_values: Tuple[float, Optional[float], Optional[float]]) -> Dict[str, Any]:
    """Format load average values for display"""
    load1, load5, load15 = load_values
    return {
        "load1": load1,
        "load5_str": f"{load5:.2f}" if load5 is not None else "N/A",
        "load15_str": f"{load15:.2f}" if load15 is not None else "N/A",
        "load5": load5,
        "load15": load15
    }


def collect_system_metrics() -> Dict[str, Any]:
    """Collect all system metrics and return as a dictionary"""
    # Get process stats
    process_stats = get_process_stats()

    # Get RAM usage
    total_ram_percent = get_total_ram_usage()
    process_ram_usage = get_ram_usage()

    # Get and format system load
    load_values = get_system_load()
    load_info = format_load_values(load_values)

    # Combine all metrics
    return {
        "memory_info": process_stats["memory_info"],
        "cpu_percent": process_stats["cpu_percent"],
        "total_ram_percent": total_ram_percent,
        "process_ram_usage": process_ram_usage,
        **load_info  # Unpack load values
    }
