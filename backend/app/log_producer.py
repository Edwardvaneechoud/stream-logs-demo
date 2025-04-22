# log_producer.py
import random
from logging import INFO, WARNING, ERROR, CRITICAL
from typing import Any, Dict

from logger import SessionLogger
from system_utils import collect_system_metrics, get_system_metrics

# Define log type weights
LOG_TYPES = [INFO, WARNING, ERROR, CRITICAL]
LOG_WEIGHTS = [0.6, 0.2, 0.15, 0.05]  # 60% INFO, 20% WARNING, 15% ERROR, 5% CRITICAL


def generate_info_message(metrics: Dict[str, Any]) -> str:
    """Generate an INFO level message with system stats"""
    # Create a consolidated system report
    system_report = (
        f"SYSTEM STATS:\n"
        f"  RAM: {metrics['total_ram_percent']:.1f}%\n"
        f"  Load Average: {metrics['load1']:.2f} (1m), {metrics['load5_str']} (5m), {metrics['load15_str']} (15m)\n"
        f"  Process: {metrics['memory_info'].rss / 1024 / 1024:.2f} MB, CPU: {metrics['cpu_percent']:.1f}%"
    )

    # Add top processes if available
    if metrics['process_ram_usage']:
        system_report += "\n  Top Memory Usage:"
        for i, (name, usage) in enumerate(list(metrics['process_ram_usage'].items())[:5], 1):
            system_report += f"\n    {i}. {name}: {usage}"

    return system_report


def generate_warning_message(metrics: Dict[str, Any]) -> str:
    """Generate a WARNING level message based on system metrics"""
    if metrics['total_ram_percent'] > 80:
        return f"⚠️ WARNING: High memory usage detected: {metrics['total_ram_percent']:.1f}%"
    elif metrics['load1'] > 2:  # Adjust threshold based on your system
        return f"⚠️ WARNING: High system load detected: {metrics['load1']:.2f}"
    elif metrics['cpu_percent'] > 50:
        return f"⚠️ WARNING: High CPU usage detected: {metrics['cpu_percent']:.1f}%"
    else:
        return f"⚠️ WARNING: Potential resource contention.\n  RAM: {metrics['total_ram_percent']:.1f}%\n  Load: {metrics['load1']:.2f}"


def generate_error_message(metrics: Dict[str, Any]) -> str:
    """Generate an ERROR level message based on system metrics"""
    if metrics['total_ram_percent'] > 90:
        return f"❌ ERROR: Critical memory pressure: {metrics['total_ram_percent']:.1f}%"
    elif metrics['load1'] > 4:  # Adjust threshold based on your system
        return f"❌ ERROR: System overloaded: {metrics['load1']:.2f}"
    else:
        error_messages = [
            "❌ ERROR: Failed to process request due to resource limitations",
            "❌ ERROR: Background task terminated unexpectedly",
            "❌ ERROR: Database connection timeout",
            "❌ ERROR: Cache synchronization failed"
        ]
        return random.choice(error_messages)


def generate_critical_message(metrics: Dict[str, Any]) -> str:
    """Generate a CRITICAL level message based on system metrics"""
    if metrics['total_ram_percent'] > 95:
        return f"🔥 CRITICAL: System memory exhausted: {metrics['total_ram_percent']:.1f}%"
    elif metrics['load1'] > 8:  # Very high load
        return f"🔥 CRITICAL: System severely overloaded: {metrics['load1']:.2f}"
    else:
        critical_messages = [
            "🔥 CRITICAL: Application service crashed",
            "🔥 CRITICAL: Database connection pool exhausted",
            "🔥 CRITICAL: Disk I/O error detected",
            "🔥 CRITICAL: Network connectivity lost"
        ]
        return random.choice(critical_messages)


def produce_log_message(session_logger: SessionLogger) -> None:
    """
    Generate and log a system monitoring message based on current metrics

    Args:
        session_logger: Session logger object
    """

    # Get metrics (either as dict or Pydantic model)

    metrics = collect_system_metrics()

    # Determine log type using weighted random choice
    log_type = random.choices(LOG_TYPES, weights=LOG_WEIGHTS, k=1)[0]

    # Generate and log message based on log type
    if log_type == INFO:
        message = generate_info_message(metrics)
        session_logger.info(message)
    elif log_type == WARNING:
        message = generate_warning_message(metrics)
        session_logger.warning(message)
    elif log_type == ERROR:
        message = generate_error_message(metrics)
        session_logger.error(message)
    elif log_type == CRITICAL:
        message = generate_critical_message(metrics)
        session_logger.critical(message)
