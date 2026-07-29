"""
Repository class managing service configurations and rich status mappings.
Supports searching, sorting, pagination, and filtering.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import Service, HealthLog
from app.repositories.base import BaseRepository
from app import schemas

class ServiceRepository(BaseRepository[Service]):
    """
    Service database repository interface.
    """

    def __init__(self):
        super().__init__(Service)

    def get_by_name(self, db: Session, name: str) -> Optional[Service]:
        """
        Retrieves a service record by its unique name identifier.
        """
        return db.query(self.model).filter(self.model.name == name).first()

    def get_by_environment(self, db: Session, environment: str) -> List[Service]:
        """
        Retrieves all services matching a specific environment level.
        """
        return db.query(self.model).filter(self.model.environment == environment).all()

    def get_multi_filtered(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        environment: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> List[Service]:
        """
        Queries service records supporting pagination, text search, environment filter, and sorting.
        """
        query = db.query(self.model)
        
        # Apply environment filter
        if environment:
            query = query.filter(self.model.environment == environment)
            
        # Apply text search on name or description
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (self.model.name.like(search_pattern)) |
                (self.model.description.like(search_pattern))
            )
            
        # Apply sorting
        if sort_by == "name":
            query = query.order_by(self.model.name.asc())
        elif sort_by == "environment":
            query = query.order_by(self.model.environment.asc())
        elif sort_by == "created_at":
            query = query.order_by(self.model.created_at.desc())
        else:
            query = query.order_by(self.model.id.asc())
            
        return query.offset(skip).limit(limit).all()

    def get_service_response(self, db: Session, service: Service) -> schemas.ServiceResponse:
        """
        Builds a rich ServiceResponse schema containing current status, availability %,
        latency timelines, SRE uptime, version details, and last success/failure timestamps.
        """
        # Fetch the latest check
        latest_log = db.query(HealthLog).filter(
            HealthLog.service_id == service.id
        ).order_by(HealthLog.timestamp.desc()).first()

        # Fetch last 100 logs for history charts and timelines
        history_logs = db.query(HealthLog).filter(
            HealthLog.service_id == service.id
        ).order_by(HealthLog.timestamp.desc()).limit(100).all()

        # Default SRE metadata values
        status = "Unknown"
        response_time = 0.0
        version = "Unknown"
        uptime_str = "Unknown"
        hostname = "Unknown"
        last_success = None
        last_failure = None

        if latest_log:
            status = latest_log.status
            response_time = latest_log.response_time
            
            # Parse SRE details stored inside the remarks column
            if latest_log.remarks and "v=" in latest_log.remarks:
                try:
                    tokens = latest_log.remarks.split("|")
                    for token in tokens:
                        if token.startswith("v="):
                            version = token.split("=")[1]
                        elif token.startswith("up="):
                            uptime_str = token.split("=")[1]
                        elif token.startswith("host="):
                            hostname = token.split("=")[1]
                except Exception:
                    pass

        # Calculate Last Success timestamp (Healthy or Warning status)
        success_check = db.query(HealthLog).filter(
            HealthLog.service_id == service.id,
            HealthLog.status.in_(["Healthy", "Warning"])
        ).order_by(HealthLog.timestamp.desc()).first()
        if success_check:
            last_success = success_check.timestamp

        # Calculate Last Failure timestamp (Critical or Offline status)
        failure_check = db.query(HealthLog).filter(
            HealthLog.service_id == service.id,
            HealthLog.status.in_(["Critical", "Offline"])
        ).order_by(HealthLog.timestamp.desc()).first()
        if failure_check:
            last_failure = failure_check.timestamp

        # Compile historical arrays (note: reverse to chronological order for charts)
        history_statuses = [log.status for log in reversed(history_logs)]
        history_latencies = [log.response_time for log in reversed(history_logs)]

        # Calculate Availability percentage
        availability = 100.0
        if history_logs:
            healthy_count = sum(1 for log in history_logs if log.status in ("Healthy", "Warning"))
            availability = round((healthy_count / len(history_logs)) * 100.0, 1)

        return schemas.ServiceResponse(
            id=service.id,
            name=service.name,
            description=service.description,
            environment=service.environment,
            health_url=service.health_url,
            ip_address=service.ip_address,
            port=service.port,
            response_time_threshold=service.response_time_threshold,
            cpu_threshold=service.cpu_threshold,
            memory_threshold=service.memory_threshold,
            created_at=service.created_at,
            updated_at=service.updated_at,
            status=status,
            response_time=response_time,
            availability=availability,
            last_success=last_success,
            last_failure=last_failure,
            version=version,
            uptime_str=uptime_str,
            hostname=hostname,
            history_statuses=history_statuses,
            history_latencies=history_latencies
        )

# Global instance for injection
service_repo = ServiceRepository()
