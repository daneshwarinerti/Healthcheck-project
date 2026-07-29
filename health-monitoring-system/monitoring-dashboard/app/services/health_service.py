"""
Health service layer using psutil to compile real-time hardware telemetry.
"""

import time
import socket
import platform
import psutil
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database.models import HealthLog, AuditLog, Service
from app.repositories.log import health_log_repo, audit_log_repo
from app.repositories.service import service_repo

class HealthService:
    """
    HealthService encapsulating hardware stats collection and database logs.
    """

    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """
        Reads real-time hardware performance metrics of the host machine using psutil.
        """
        # 1. CPU Telemetry
        # interval=None ensures it is non-blocking and returns instantaneous value
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_cores = psutil.cpu_count(logical=True) or 1
        
        # 2. Memory Telemetry
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_used = round(mem.used / (1024 ** 3), 2)  # Convert to GB
        mem_total = round(mem.total / (1024 ** 3), 2)
        
        # 3. Disk Telemetry
        try:
            disk = psutil.disk_usage('/')
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
        boot_seconds = time.time() - psutil.boot_time()
        days, remainder = divmod(int(boot_seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            uptime_str = f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            uptime_str = f"{hours}h {minutes}m"
        else:
            uptime_str = f"{minutes}m {seconds}s"
            
        return {
            "cpu_percent": cpu_percent,
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
            "hostname": socket.gethostname(),
            "platform": f"{platform.system()} {platform.release()}",
            "python_version": platform.python_version()
        }

    @staticmethod
    def query_health_logs(
        db: Session, 
        service_id: Optional[int] = None, 
        status: Optional[str] = None, 
        skip: int = 0,
        limit: int = 100
    ) -> List[HealthLog]:
        """
        Queries health check logs with optional service, status, pagination filters.
        """
        query = db.query(HealthLog)
        
        if service_id is not None:
            query = query.filter(HealthLog.service_id == service_id)
        if status is not None and status != "All":
            query = query.filter(HealthLog.status == status)
            
        return query.order_by(HealthLog.timestamp.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def query_audit_logs(
        db: Session, 
        action: Optional[str] = None, 
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Queries audit trail action entries supporting pagination.
        """
        query = db.query(AuditLog)
        if action is not None and action != "All":
            query = query.filter(AuditLog.action == action)
            
        return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
