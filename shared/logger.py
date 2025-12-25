"""
Centralized Logging for HealthLink360
Provides structured logging with audit trail capabilities
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from loguru import logger
from typing import Optional, Dict, Any

from shared.config import settings


class HealthLinkLogger:
    """Custom logger for HealthLink360 with audit capabilities"""
    
    def __init__(self):
        # Remove default logger
        logger.remove()
        
        # Console logging
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level=settings.log_level,
            colorize=True
        )
        
        # File logging - General
        log_path = Path(settings.log_dir) / "healthlink360_{time:YYYY-MM-DD}.log"
        logger.add(
            log_path,
            rotation="00:00",  # Rotate daily
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
            level=settings.log_level
        )
        
        # File logging - Errors only
        error_log_path = Path(settings.log_dir) / "errors_{time:YYYY-MM-DD}.log"
        logger.add(
            error_log_path,
            rotation="00:00",
            retention="90 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
            level="ERROR"
        )
        
        # Audit logging (if enabled)
        if settings.enable_audit_logging:
            audit_log_path = Path(settings.log_dir) / "audit_{time:YYYY-MM-DD}.log"
            logger.add(
                audit_log_path,
                rotation="00:00",
                retention=f"{settings.audit_log_retention_days} days",
                compression="zip",
                format="{message}",  # JSON format
                level="INFO",
                filter=lambda record: record["extra"].get("audit", False)
            )
        
        self.logger = logger
    
    def audit(
        self,
        user_id: Optional[str],
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        success: bool = True
    ):
        """
        Log an audit event
        
        Args:
            user_id: ID of the user performing the action
            action: Action performed (e.g., "CREATE", "READ", "UPDATE", "DELETE")
            resource: Resource type (e.g., "patient", "prescription", "report")
            resource_id: ID of the specific resource
            details: Additional details about the action
            ip_address: IP address of the requester
            success: Whether the action was successful
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "success": success
        }
        
        self.logger.bind(audit=True).info(json.dumps(audit_entry))
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, **kwargs)


# Global logger instance
app_logger = HealthLinkLogger()
