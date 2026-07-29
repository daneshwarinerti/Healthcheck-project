"""
Database seeder script generating default Admin accounts and target services configurations.
"""

import sys
import os

# Append current directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal, engine
from app.database.models import Base, User, Service, HealthLog
from app.core.security import get_password_hash
from app.core.logging import setup_logging, app_logger

def seed_db() -> None:
    """
    Seeds database with default system operators and monitored nodes.
    """
    setup_logging()
    
    try:
        # Create database tables if they do not exist yet in PostgreSQL
        Base.metadata.create_all(bind=engine)
        app_logger.info("Seeder: Verified database schema tables exist.")
    except Exception as table_err:
        app_logger.warning(f"Seeder: Table creation note: {table_err}")
        
    db: Session = SessionLocal()
    
    try:
        app_logger.info("Seeder: Starting database seeding sequence...")
        
        # 1. Seed Default Admin User
        admin_email = "admin@example.com"
        admin_user = db.query(User).filter(User.email == admin_email).first()
        if not admin_user:
            app_logger.info(f"Seeder: Creating default administrator '{admin_email}'...")
            admin_user = User(
                first_name="Devops",
                last_name="Admin",
                email=admin_email,
                hashed_password=get_password_hash("Admin@123"),
                role="Admin"
            )
            db.add(admin_user)
        else:
            app_logger.info(f"Seeder: Administrator '{admin_email}' already exists.")
            
        # 2. Seed Default Operator User (Useful for testing RBAC)
        op_email = "operator@example.com"
        op_user = db.query(User).filter(User.email == op_email).first()
        if not op_user:
            app_logger.info(f"Seeder: Creating default operator '{op_email}'...")
            op_user = User(
                first_name="SRE",
                last_name="Operator",
                email=op_email,
                hashed_password=get_password_hash("Operator@123"),
                role="Operator"
            )
            db.add(op_user)
        else:
            app_logger.info(f"Seeder: Operator '{op_email}' already exists.")

        # 3. Seed Default Monitored Services configurations
        user_svc_url = os.getenv("USER_SERVICE_URL", "http://user-service:8001/health")
        payment_svc_url = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8002/health")
        notification_svc_url = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8003/health")
        postgres_svc_url = os.getenv("POSTGRES_HEALTH_URL", "postgres:5432")
        redis_svc_url = os.getenv("REDIS_HEALTH_URL", "redis:6379")
        rabbitmq_svc_url = os.getenv("RABBITMQ_HEALTH_URL", "rabbitmq:5672")

        default_services = [
            {
                "name": "User Service",
                "description": "User profile management and identity validation API microservice.",
                "environment": "Production",
                "health_url": user_svc_url,
                "ip_address": "user-service",
                "port": 8001,
                "response_time_threshold": 1000
            },
            {
                "name": "Payment Service",
                "description": "Financial transaction ledger and stripe payment gateways portal.",
                "environment": "Production",
                "health_url": payment_svc_url,
                "ip_address": "payment-service",
                "port": 8002,
                "response_time_threshold": 1000
            },
            {
                "name": "Notification Service",
                "description": "E-mail dispatches, Slack notifications and SMS broadcast API.",
                "environment": "Production",
                "health_url": notification_svc_url,
                "ip_address": "notification-service",
                "port": 8003,
                "response_time_threshold": 1000
            },
            {
                "name": "PostgreSQL Database",
                "description": "Primary relational storage database server cluster.",
                "environment": "Production",
                "health_url": postgres_svc_url,
                "ip_address": "postgres",
                "port": 5432,
                "response_time_threshold": 500
            },
            {
                "name": "Redis Broker",
                "description": "Distributed cache memory database and locks synchronization server.",
                "environment": "Production",
                "health_url": redis_svc_url,
                "ip_address": "redis",
                "port": 6379,
                "response_time_threshold": 200
            },
            {
                "name": "RabbitMQ Queue",
                "description": "Asynchronous messaging queue and tasks worker broker.",
                "environment": "Production",
                "health_url": rabbitmq_svc_url,
                "ip_address": "rabbitmq",
                "port": 5672,
                "response_time_threshold": 800
            }
        ]
        
        for svc_data in default_services:
            existing_svc = db.query(Service).filter(Service.name == svc_data["name"]).first()
            if not existing_svc:
                app_logger.info(f"Seeder: Registering target service: '{svc_data['name']}'...")
                new_svc = Service(
                    name=svc_data["name"],
                    description=svc_data["description"],
                    environment=svc_data["environment"],
                    health_url=svc_data["health_url"],
                    ip_address=svc_data["ip_address"],
                    port=svc_data["port"],
                    response_time_threshold=svc_data["response_time_threshold"],
                    cpu_threshold=90.0,
                    memory_threshold=90.0
                )
                db.add(new_svc)
            else:
                # Update existing service health_url if it currently uses localhost
                if "localhost" in existing_svc.health_url or existing_svc.ip_address == "127.0.0.1":
                    existing_svc.health_url = svc_data["health_url"]
                    existing_svc.ip_address = svc_data["ip_address"]
                    app_logger.info(f"Seeder: Updated Service '{svc_data['name']}' URL to '{svc_data['health_url']}'.")
                else:
                    app_logger.info(f"Seeder: Service '{svc_data['name']}' already registered.")
                
        db.commit()
        app_logger.info("Seeder: Seeding sequence finished successfully.")
        
    except Exception as ex:
        app_logger.error(f"Seeder: Error executing database seeding: {str(ex)}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
