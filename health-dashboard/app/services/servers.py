"""
Server service layer handling server CRUD operations, statistics compiling, and health simulations.
"""

import random
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app import models, schemas

logger = logging.getLogger("app")

class ServerService:
    """
    Service class encapsulating server management and metrics simulation.
    """

    @staticmethod
    def get_all_servers(db: Session) -> List[models.Server]:
        """
        Retrieves all configured servers from the database.
        """
        return db.query(models.Server).all()

    @staticmethod
    def get_server_by_id(db: Session, server_id: int) -> models.Server:
        """
        Retrieves a single server by its ID. Raises 404 if not found.
        """
        server = db.query(models.Server).filter(models.Server.id == server_id).first()
        if not server:
            logger.warning(f"ServerService: Server with ID {server_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with ID {server_id} not found."
            )
        return server

    @staticmethod
    def create_server(db: Session, server_in: schemas.ServerCreate) -> models.Server:
        """
        Registers a new server. Prevents duplicate server names.
        """
        logger.info(f"ServerService: Request to create server '{server_in.name}'")
        
        # Check name conflict
        existing = db.query(models.Server).filter(
            models.Server.name == server_in.name
        ).first()
        
        if existing:
            logger.warning(f"ServerService: Duplicate server name '{server_in.name}'")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Server with name '{server_in.name}' already exists."
            )
            
        # Seed initial metrics (starts as Healthy)
        initial_cpu = float(random.randint(10, 65))
        initial_memory = float(random.randint(15, 70))
        
        db_server = models.Server(
            name=server_in.name,
            environment=server_in.environment,
            ip_address=str(server_in.ip_address),  # Convert IPvAnyAddress to string
            status="Healthy",
            cpu_usage=initial_cpu,
            memory_usage=initial_memory,
            uptime=random.randint(1, 10),
            last_checked=datetime.utcnow()
        )
        
        db.add(db_server)
        db.commit()
        db.refresh(db_server)
        
        logger.info(f"ServerService: Successfully created server '{db_server.name}'")
        return db_server

    @staticmethod
    def update_server(db: Session, server_id: int, server_in: schemas.ServerUpdate) -> models.Server:
        """
        Updates an existing server's metadata. Prevents name conflicts.
        """
        logger.info(f"ServerService: Request to update server ID {server_id}")
        db_server = ServerService.get_server_by_id(db, server_id)
        
        # If renaming, verify new name is unique
        if server_in.name is not None:
            existing = db.query(models.Server).filter(
                models.Server.name == server_in.name,
                models.Server.id != server_id
            ).first()
            if existing:
                logger.warning(f"ServerService: Name conflict during update. '{server_in.name}' already exists.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Server with name '{server_in.name}' already exists."
                )

        # Apply properties
        update_data = server_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "ip_address" and value is not None:
                setattr(db_server, field, str(value))
            else:
                setattr(db_server, field, value)
                
        db_server.last_checked = datetime.utcnow()
        
        db.commit()
        db.refresh(db_server)
        logger.info(f"ServerService: Successfully updated server '{db_server.name}'")
        return db_server

    @staticmethod
    def delete_server(db: Session, server_id: int) -> None:
        """
        Removes a server registration from monitoring configs.
        """
        logger.info(f"ServerService: Request to delete server ID {server_id}")
        db_server = ServerService.get_server_by_id(db, server_id)
        
        db.delete(db_server)
        db.commit()
        logger.info(f"ServerService: Successfully deleted server ID {server_id}")

    @staticmethod
    def get_dashboard_summary(db: Session) -> schemas.DashboardSummary:
        """
        Compiles aggregated system stats.
        """
        servers = db.query(models.Server).all()
        total = len(servers)
        
        healthy = sum(1 for s in servers if s.status == "Healthy")
        unhealthy = total - healthy
        
        avg_cpu = sum(s.cpu_usage for s in servers) / total if total > 0 else 0.0
        avg_memory = sum(s.memory_usage for s in servers) / total if total > 0 else 0.0
        
        return schemas.DashboardSummary(
            total_servers=total,
            healthy_servers=healthy,
            unhealthy_servers=unhealthy,
            avg_cpu=round(avg_cpu, 1),
            avg_memory=round(avg_memory, 1)
        )

    @staticmethod
    def update_simulated_metrics(db: Session) -> None:
        """
        Refreshes server usage simulation. Applies custom health status thresholds:
        - Healthy: CPU < 70 and Memory < 75
        - Warning: CPU 70-85 or Memory 75-90 (neither exceeds critical threshold)
        - Critical: CPU > 85 or Memory > 90
        - Offline: 5% chance of simulated failure.
        """
        servers = db.query(models.Server).all()
        for s in servers:
            # 5% chance to fall offline
            if random.random() < 0.05:
                s.status = "Offline"
                s.cpu_usage = 0.0
                s.memory_usage = 0.0
            else:
                s.cpu_usage = float(random.randint(5, 100))
                s.memory_usage = float(random.randint(10, 100))
                
                # Check status thresholds
                if s.cpu_usage > 85 or s.memory_usage > 90:
                    s.status = "Critical"
                elif (70 <= s.cpu_usage <= 85) or (75 <= s.memory_usage <= 90):
                    s.status = "Warning"
                else:
                    s.status = "Healthy"
                
                # 5% chance of incrementing uptime
                if random.random() < 0.05:
                    s.uptime += 1
                    
            s.last_checked = datetime.utcnow()
        db.commit()
