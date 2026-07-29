"""
Monitoring service layer handling APScheduler execution, HTTP/socket probes, and alerts.
"""

import time
import socket
import asyncio
import logging
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database.session import SessionLocal
from app.database.models import Service, HealthLog
from app.repositories.service import service_repo
from app.repositories.log import health_log_repo, audit_log_repo
from app.core.logging import health_logger, audit_logger, scheduler_logger as logger
scheduler = AsyncIOScheduler()

async def probe_service(
    service_id: int, 
    name: str, 
    health_url: str, 
    threshold_ms: int
) -> Tuple[int, str, float, Optional[int], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Asynchronously probes a single service.
    Supports HTTP(S) URLs and direct TCP sockets (host:port).
    Returns:
        Tuple: (service_id, status, response_time_ms, http_status, remarks, version, uptime_str, hostname)
    """
    start_time = time.perf_counter()
    url_stripped = health_url.strip()
    
    # 1. HTTP health check
    if url_stripped.startswith(("http://", "https://")):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url_stripped)
                latency = round((time.perf_counter() - start_time) * 1000.0, 2)
                
                # Default SRE outputs
                version = "Unknown"
                uptime_str = "Unknown"
                hostname = "Unknown"
                remarks = None
                
                # Check JSON details
                try:
                    data = res.json()
                    version = data.get("version", "Unknown")
                    uptime_str = data.get("uptime", "Unknown")
                    hostname = data.get("hostname", "Unknown")
                except Exception:
                    pass
                
                # Evaluate HTTP Status
                if res.status_code != 200:
                    status = "Critical"
                    remarks = f"HTTP Error Status: {res.status_code}"
                else:
                    # Evaluate Latency thresholds
                    if latency < 500:
                        status = "Healthy"
                    elif latency <= threshold_ms:
                        status = "Warning"
                    else:
                        status = "Critical"
                        remarks = f"High Latency: {latency} ms (Limit: {threshold_ms} ms)"
                        
                return service_id, status, latency, res.status_code, remarks, version, uptime_str, hostname
                
        except httpx.RequestError as ex:
            latency = round((time.perf_counter() - start_time) * 1000.0, 2)
            remarks = f"Connection Failed: {type(ex).__name__}"
            return service_id, "Offline", latency, None, remarks, None, None, None
            
    # 2. TCP Socket health check
    else:
        try:
            parts = url_stripped.split(":")
            host = parts[0]
            port = int(parts[1])
            
            # Connect via TCP stream
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), 
                timeout=5.0
            )
            writer.close()
            await writer.wait_closed()
            
            latency = round((time.perf_counter() - start_time) * 1000.0, 2)
            
            # Evaluate Latency thresholds for TCP socket
            if latency < 500:
                status = "Healthy"
            elif latency <= threshold_ms:
                status = "Warning"
            else:
                status = "Critical"
                remarks = f"High Latency: {latency} ms (Limit: {threshold_ms} ms)"
                
            return service_id, status, latency, None, None, "1.0.0", "N/A", host
            
        except Exception as ex:
            latency = round((time.perf_counter() - start_time) * 1000.0, 2)
            remarks = f"Socket connection failed: {str(ex)}"
            return service_id, "Offline", latency, None, remarks, None, None, None


async def execute_health_checks() -> None:
    """
    APScheduler job that executes concurrent health checks on all registered services.
    Saves results to the database and audits service state transitions.
    """
    db: Session = SessionLocal()
    try:
        services = db.query(Service).all()
        if not services:
            return
            
        health_logger.info(f"MonitoringService: Triggering concurrent checks on {len(services)} services...")
        
        # Dispatch parallel checks
        tasks = [
            probe_service(s.id, s.name, s.health_url, s.response_time_threshold)
            for s in services
        ]
        results = await asyncio.gather(*tasks)
        
        # Log results sequentially in database
        for service_id, status, latency, http_status, remarks, version, uptime, hostname in results:
            service = db.query(Service).filter(Service.id == service_id).first()
            if not service:
                continue
                
            # Get latest check log to inspect state transition
            last_log = db.query(HealthLog).filter(
                HealthLog.service_id == service_id
            ).order_by(HealthLog.timestamp.desc()).first()
            
            # Audit state transition (Healthy <-> Warning <-> Critical <-> Offline)
            if last_log and last_log.status != status:
                action_text = "Service Status Changed"
                details_text = f"Service '{service.name}' transitioned from {last_log.status} to {status}."
                if remarks:
                    details_text += f" Reason: {remarks}"
                
                # Check for recovery
                if status == "Healthy" and last_log.status in ("Offline", "Critical"):
                    action_text = "Service Recovered"
                    details_text = f"Service '{service.name}' recovered successfully to Healthy status ({latency} ms)."
                    
                audit_log_repo.log_action(
                    db,
                    user_id=None,  # System event
                    action=action_text,
                    details=details_text,
                    ip_address="127.0.0.1"
                )
                audit_logger.warning(f"MonitoringService: {details_text}")
            
            # Combine SRE metadata into a single string for storage
            remarks_packed = f"v={version or '1.0.0'}|up={uptime or 'N/A'}|host={hostname or 'N/A'}"
            if remarks:
                remarks_packed += f"|err={remarks}"
            
            # Save health log record
            new_log = HealthLog(
                service_id=service_id,
                status=status,
                response_time=latency,
                http_status=http_status,
                remarks=remarks_packed,
                timestamp=datetime.utcnow()
            )
            db.add(new_log)
            
            # Print SRE log
            log_msg = f"Check: {service.name} [{status}] - Latency: {latency} ms"
            if remarks:
                log_msg += f" - Remarks: {remarks}"
            if status in ("Critical", "Offline"):
                health_logger.error(log_msg)
            else:
                health_logger.info(log_msg)
                
        db.commit()
    except Exception as ex:
        logger.error(f"MonitoringService: Error in check scheduler execution: {str(ex)}", exc_info=True)
        db.rollback()
    finally:
        db.close()


class MonitoringService:
    """
    Manager class to start and stop the SRE monitoring cron engine.
    """
    
    @staticmethod
    def start_scheduler() -> None:
        """
        Registers the health check runner in APScheduler and starts the daemon thread.
        """
        # Ensure job is not duplicated
        if not scheduler.get_job("health_check_job"):
            scheduler.add_job(
                execute_health_checks,
                "interval",
                seconds=15,
                id="health_check_job"
            )
            scheduler.start()
            logger.info("MonitoringService: Started SRE monitoring scheduler daemon")

    @staticmethod
    def stop_scheduler() -> None:
        """
        Gracefully terminates the background APScheduler thread.
        """
        if scheduler.running:
            scheduler.shutdown()
            logger.info("MonitoringService: Stopped SRE monitoring scheduler daemon")
            
    @staticmethod
    def trigger_immediate_checks() -> None:
        """
        Triggers an immediate execution of all monitoring tasks asynchronously.
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(execute_health_checks())
