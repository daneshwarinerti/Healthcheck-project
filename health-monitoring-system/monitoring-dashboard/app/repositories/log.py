"""
Repository classes managing health checks and audit logs database transactions.
"""

from typing import Any, List, Optional
from sqlalchemy.orm import Session
from app.database.models import AuditLog, HealthLog
from app.repositories.base import BaseRepository

class HealthLogRepository(BaseRepository[HealthLog]):
    """
    HealthLog database repository interface.
    """

    def __init__(self):
        super().__init__(HealthLog)

    def get_last_logs_for_service(
        self, db: Session, service_id: int, limit: int = 100
    ) -> List[HealthLog]:
        """
        Retrieves the last N health check logs for a specific service,
        sorted chronologically (newest first).
        """
        return db.query(self.model).filter(
            self.model.service_id == service_id
        ).order_by(self.model.timestamp.desc()).limit(limit).all()

    def get_availability_percentage(self, db: Session, service_id: int, limit: int = 100) -> float:
        """
        Calculates the availability ratio (Healthy checks / Total checks) over the last N checks.
        """
        logs = self.get_last_logs_for_service(db, service_id, limit)
        if not logs:
            return 100.0
        
        healthy_count = sum(1 for log in logs if log.status in ("Healthy", "Warning"))
        return round((healthy_count / len(logs)) * 100.0, 1)


class AuditLogRepository(BaseRepository[AuditLog]):
    """
    AuditLog database repository interface.
    """

    def __init__(self):
        super().__init__(AuditLog)

    def log_action(
        self, 
        db: Session, 
        user_id: Optional[int], 
        action: str, 
        details: str, 
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Helper method to quickly insert a user action log into the audit ledger.
        """
        obj_in_data = {
            "user_id": user_id,
            "action": action,
            "details": details,
            "ip_address": ip_address
        }
        return self.create(db, obj_in_data=obj_in_data)

    def get_recent_audit_logs(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[AuditLog]:
        """
        Retrieves recent audit logs sorted by newest timestamp first.
        """
        return db.query(self.model).order_by(self.model.timestamp.desc()).offset(skip).limit(limit).all()

# Global instances for injection
health_log_repo = HealthLogRepository()
audit_log_repo = AuditLogRepository()
