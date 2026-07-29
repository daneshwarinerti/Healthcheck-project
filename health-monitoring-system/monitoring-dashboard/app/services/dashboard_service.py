"""
Dashboard service layer aggregating status counts and compile alert timeline records.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.database.models import Service, HealthLog, AuditLog
from app.services.health_service import HealthService
from app.schemas.metrics import DashboardSummary, AlertTimelineItem, SystemMetricsResponse
from app.repositories.service import service_repo
from app.repositories.log import health_log_repo

class DashboardService:
    """
    DashboardService encapsulating aggregation tasks.
    """

    @staticmethod
    def get_dashboard_summary(db: Session) -> DashboardSummary:
        """
        Compiles the unified SRE dashboard state payload.
        """
        # 1. Fetch all monitored services
        services = service_repo.get_multi(db)
        total = len(services)
        
        healthy = 0
        warning = 0
        critical = 0
        offline = 0
        unknown = 0
        
        total_latency = 0.0
        active_latencies_count = 0
        
        for s in services:
            # Query latest check outcome
            latest_check = db.query(HealthLog).filter(
                HealthLog.service_id == s.id
            ).order_by(HealthLog.timestamp.desc()).first()
            
            if not latest_check:
                unknown += 1
            else:
                status = latest_check.status
                if status == "Healthy":
                    healthy += 1
                elif status == "Warning":
                    warning += 1
                elif status == "Critical":
                    critical += 1
                elif status == "Offline":
                    offline += 1
                else:
                    unknown += 1
                
                # Exclude offline or unknown from average latency
                if status != "Offline" and latest_check.response_time > 0:
                    total_latency += latest_check.response_time
                    active_latencies_count += 1
                    
        avg_response = round(total_latency / active_latencies_count, 1) if active_latencies_count > 0 else 0.0
        
        # 2. Get hardware telemetry snapshot
        system_stats = HealthService.get_system_metrics()
        system_schema = SystemMetricsResponse(**system_stats)
        
        # 3. Compile chronological SRE alerts timeline (from audit log transitions)
        alert_logs = db.query(AuditLog).filter(
            AuditLog.action.in_(["Service Status Changed", "Service Recovered"])
        ).order_by(AuditLog.timestamp.desc()).limit(15).all()
        
        alerts_feed: List[AlertTimelineItem] = []
        for log in alert_logs:
            # Determine alert severity level class
            log_lower = log.details.lower() if log.details else ""
            
            if "offline" in log_lower:
                badge_type = "danger"
            elif "critical" in log_lower:
                badge_type = "danger"
            elif "warning" in log_lower:
                badge_type = "warning"
            elif "recovered" in log_lower or "healthy" in log_lower:
                badge_type = "success"
            else:
                badge_type = "secondary"
                
            # Extract service name if possible (Service 'Payment API' ...)
            service_name = "System Alert"
            if "service '" in log_lower:
                try:
                    start_idx = log.details.index("service '") + 9
                    end_idx = log.details.index("'", start_idx)
                    service_name = log.details[start_idx:end_idx]
                except ValueError:
                    pass
            
            time_formatted = log.timestamp.strftime("%H:%M")
            alerts_feed.append(
                AlertTimelineItem(
                    timestamp=time_formatted,
                    service_name=service_name,
                    message=log.details or "",
                    type=badge_type
                )
            )
            
        return DashboardSummary(
            total_services=total,
            healthy_services=healthy,
            warning_services=warning,
            critical_services=critical,
            offline_services=offline,
            unknown_services=unknown,
            avg_response_time=avg_response,
            system=system_schema,
            alerts=alerts_feed
        )
