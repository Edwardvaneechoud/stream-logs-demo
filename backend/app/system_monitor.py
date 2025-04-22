# system_monitor.py
import threading
import time
import random
import logging
from app.logger import SessionLogger
from app.system_utils import collect_system_metrics

main_logger = logging.getLogger('StreamLogger')


class SystemMonitor:
    """
    Monitor system metrics and log them using the provided logger
    """
    _monitoring: bool
    _monitor_thread: threading.Thread | None
    session_logger: SessionLogger | None

    def __init__(self, session_logger: SessionLogger):
        """
        Initialize the system monitor

        Args:
            session_logger: object with info(), warning(), and error() methods
        """
        self.session_logger = session_logger
        self._monitoring = False
        self._monitor_thread = None
        self._lock = threading.RLock()

    def start(self, interval: int = 2) -> None:
        """
        Start the monitoring thread

        Args:
            interval: Time between log entries in seconds
        """
        with self._lock:
            if self._monitoring:
                return

            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                args=(interval,),
                daemon=True
            )
            self._monitor_thread.start()
            self.session_logger.info(f"Started system monitoring with interval: {interval}s")

    def stop(self) -> None:
        """Stop the monitoring thread"""
        with self._lock:
            if not self._monitoring:
                return

            self._monitoring = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=2)
                self._monitor_thread = None
                self.session_logger.info("Stopped system monitoring")

    def _monitoring_loop(self, interval: int) -> None:
        """Main monitoring loop that runs in a separate thread"""
        log_types = ["INFO", "WARNING", "ERROR"]
        log_weights = [0.7, 0.2, 0.1]  # 70% INFO, 20% WARNING, 10% ERROR

        while self._monitoring:
            try:
                # Collect metrics
                metrics = collect_system_metrics()

                # Determine log type using weighted random choice
                log_type = random.choices(log_types, weights=log_weights, k=1)[0]

                # Generate and log message based on type
                if log_type == "INFO":
                    self._log_info_message(metrics)
                elif log_type == "WARNING":
                    self._log_warning_message(metrics)
                elif log_type == "ERROR":
                    self._log_error_message(metrics)

                # Add some randomization to the interval
                time.sleep(interval + random.uniform(-0.5, 0.5))
            except Exception as e:
                main_logger.error(f"Error in monitoring thread: {e}")
                time.sleep(interval)

    def _log_info_message(self, metrics: dict) -> None:
        """Generate and log an INFO level message with system stats"""
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

        self.session_logger.info(system_report)

    def _log_warning_message(self, metrics: dict) -> None:
        """Generate and log a WARNING level message based on system metrics"""
        if metrics['total_ram_percent'] > 80:
            self.session_logger.warning(f"High memory usage detected: {metrics['total_ram_percent']:.1f}%")
        elif metrics['load1'] > 2:  # Adjust threshold based on your system
            self.session_logger.warning(f"High system load detected: {metrics['load1']:.2f}")
        elif metrics['cpu_percent'] > 50:
            self.session_logger.warning(f"High CPU usage detected: {metrics['cpu_percent']:.1f}%")
        else:
            self.session_logger.warning(f"Potential resource contention.\n  RAM: {metrics['total_ram_percent']:.1f}%\n  Load: {metrics['load1']:.2f}")

    def _log_error_message(self, metrics: dict) -> None:
        """Generate and log an ERROR level message based on system metrics"""
        if metrics['total_ram_percent'] > 90:
            self.session_logger.error(f"Critical memory pressure: {metrics['total_ram_percent']:.1f}%")
        elif metrics['load1'] > 4:  # Adjust threshold based on your system
            self.session_logger.error(f"System overloaded: {metrics['load1']:.2f}")
        else:
            error_messages = [
                "Failed to process request due to resource limitations",
                "Background task terminated unexpectedly",
                "Database connection timeout",
                "Cache synchronization failed"
            ]
            self.session_logger.error(random.choice(error_messages))
