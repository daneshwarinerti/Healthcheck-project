"""
Core SRE logging configuration script.
Splits logger outputs into four separate files in the 'logs/' directory:
- logs/application.log
- logs/health.log
- logs/audit.log
- logs/scheduler.log
"""

import os
import sys
import logging

def setup_logging() -> None:
    """
    Sets up SRE separated logging channels.
    Creates files for application events, health logs, audits, and task schedules.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    formatter = logging.Formatter(log_format)
    
    # 1. Create logs directory safely
    try:
        os.makedirs("logs", exist_ok=True)
    except Exception as e:
        print(f"Logging Notice: File logging initialization deferred: {e}")
    
    # Configure base root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing base handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    # Shared console handler to trace all loggers in stdout streams
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    def configure_sre_logger(logger_name: str, file_path: str) -> None:
        """
        Attaches a console stream handler and a separate file handler to a named logger.
        """
        target_logger = logging.getLogger(logger_name)
        target_logger.setLevel(logging.INFO)
        target_logger.propagate = False  # Avoid duplicates on root logger
        
        # Console output
        target_logger.addHandler(console_handler)
        
        # File output
        try:
            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            target_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Logging: Failed to initialize file logging handler for '{file_path}': {str(e)}")

    # Attach split outputs to respective loggers
    configure_sre_logger("app", "logs/application.log")
    configure_sre_logger("health_checks", "logs/health.log")
    configure_sre_logger("audit", "logs/audit.log")
    configure_sre_logger("scheduler", "logs/scheduler.log")
    configure_sre_logger("app_errors", "logs/application.log")
    
    # Re-route APScheduler default log output to scheduler.log
    configure_sre_logger("apscheduler", "logs/scheduler.log")

# Retrieve specialized loggers
app_logger = logging.getLogger("app")
health_logger = logging.getLogger("health_checks")
audit_logger = logging.getLogger("audit")
scheduler_logger = logging.getLogger("scheduler")
error_logger = logging.getLogger("app_errors")
