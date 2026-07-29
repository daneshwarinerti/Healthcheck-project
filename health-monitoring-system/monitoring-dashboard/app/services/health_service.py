"""
Health service layer using psutil to compile real-time hardware telemetry.
"""

import os
import time
import socket
import platform
import psutil
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import HealthLog, AuditLog, Service
from app.repositories.log import health_log_repo, audit_log_repo
from app.repositories.service import service_repo

# Warm up psutil CPU calculation on module load
try:
    psutil.cpu_percent(interval=None)
except Exception:
    pass

class HealthService:
    """
    HealthService encapsulating hardware stats collection and database logs.
    """

    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """
        Reads real-time hardware performance metrics of the host machine using psutil.
        Cross-platform compatible with Windows, Linux, and macOS.
        """
        # 1. CPU Telemetry
        cpu_percent = psutil.cpu_percent(interval=None)
        if cpu_percent == 0.0:
            time.sleep(0.02)
            cpu_percent = psutil.cpu_percent(interval=None)
            
        cpu_cores = psutil.cpu_count(logical=True) or 1
        
        # 2. Memory Telemetry
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_used = round(mem.used / (1024 ** 3), 2)  # Convert to GB
        mem_total = round(mem.total / (1024 ** 3), 2)
        
        # 3. Disk Telemetry (Cross-platform root pathing)
        try:
            root_path = os.path.abspath(os.sep)
            disk = psutil.disk_usage(root_path)
            disk_percent = disk.percent
            disk_used = round(disk.used / (1024 ** 3), 2)
            disk_total = round(disk.total / (1024 ** 3), 2)
        except Exception:
            disk_percent = 0.0
            disk_used = 0.0
            disk_total = 0.0
            
        # 4. Network Telemetry
        try:
            net = psutil.net_io_counters()
            net_sent = round(net.bytes_sent / (1024 ** 2), 2)  # Convert to MB
            net_recv = round(net.bytes_recv / (1024 ** 2), 2)
        except Exception:
            net_sent = 0.0
            net_recv = 0.0
            
        # 5. Uptime Calculation
        try:
            boot_seconds = time.time() - psutil.boot_time()
            days, remainder = divmod(int(boot_seconds), 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{days}d {hours}h {minutes}m"
        except Exception:
            uptime_str = "Unknown"

        # 6. Host System Platform Telemetry
        try:
            hostname = socket.gethostname()
        except Exception:
            hostname = "localhost"

        return {
            "cpu_percent": round(cpu_percent, 1),
            "cpu_cores": cpu_cores,
            "memory_percent": mem_percent,
            "memory_used_gb": mem_used,
            "memory_total_gb": mem_total,
            "disk_percent": disk_percent,
            "disk_used_gb": disk_used,
            "disk_total_gb": disk_total,
            "network_sent_mb": net_sent,
            "network_recv_mb": net_recv,
            "system_uptime": uptime_str,
            "hostname": hostname,
            "platform": f"{platform.system()} {platform.release()}",
            "python_version": platform.python_version()
        }

    @staticmethod
    def execute_tcp_ping(host: str, port: int, timeout: float = 3.0) -> tuple:
        """
        Executes a socket connection probe to measure round-trip latency.
        """
        start = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            s.close()
            latency = round((time.time() - start) * 1000, 2)
            return True, latency, 200, "Connection established successfully."
        except socket.timeout:
            return False, 0.0, 504, f"Socket connection timeout after {timeout}s."
        except ConnectionRefusedError:
            return False, 0.0, 601, f"Connection refused at {host}:{port}."
        except Exception as ex:
            return False, 0.0, 500, f"Socket error: {str(ex)}"
