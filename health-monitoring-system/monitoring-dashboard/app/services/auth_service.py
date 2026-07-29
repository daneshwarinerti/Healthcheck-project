"""
Auth service layer handling registration validation, credentials checks, and audit trails.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.database.models import User, AuditLog
from app.repositories.user import user_repo
from app.repositories.log import audit_log_repo
from app.schemas.user import UserRegister, UserLogin
from app.core import security
from app.core.logging import audit_logger

class AuthService:
    """
    AuthService encapsulating registration validations, credentials matching, and audits.
    """

    @staticmethod
    def register_user(
        db: Session, 
        user_in: UserRegister, 
        ip_address: Optional[str] = None
    ) -> User:
        """
        Registers a new user after verifying that the email address is unique.
        """
        audit_logger.info(f"AuthService: Registering new user account: '{user_in.email}'")
        
        # Check duplicate email
        existing_user = user_repo.get_by_email(db, user_in.email)
        if existing_user:
            audit_logger.warning(f"AuthService: Registration failed. Email '{user_in.email}' is already taken.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user account with this email address already exists."
            )
            
        hashed_password = security.get_password_hash(user_in.password)
        obj_in_data = {
            "first_name": user_in.first_name,
            "last_name": user_in.last_name,
            "email": user_in.email,
            "hashed_password": hashed_password,
            "role": user_in.role or "Viewer"
        }
        
        new_user = user_repo.create(db, obj_in_data=obj_in_data)
        
        # Log action in audit trail
        audit_log_repo.log_action(
            db,
            user_id=new_user.id,
            action="User Registered",
            details=f"Created account for {new_user.email} with role {new_user.role}",
            ip_address=ip_address
        )
        
        audit_logger.info(f"AuthService: Successfully registered user ID {new_user.id}")
        return new_user

    @staticmethod
    def authenticate_user(
        db: Session, 
        credentials: UserLogin, 
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verifies login credentials and returns a JWT access token.
        """
        audit_logger.info(f"AuthService: Login attempt for email '{credentials.email}'")
        
        user = user_repo.get_by_email(db, credentials.email)
        if not user or not security.verify_password(credentials.password, user.hashed_password):
            audit_logger.warning(f"AuthService: Failed login attempt for email '{credentials.email}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        # Issue token
        token_data = {"sub": user.email, "role": user.role}
        access_token = security.create_access_token(data=token_data)
        
        # Log to audit trail
        audit_log_repo.log_action(
            db,
            user_id=user.id,
            action="User Login",
            details=f"Successful login for {user.email}",
            ip_address=ip_address
        )
        
        audit_logger.info(f"AuthService: Successful login for email '{credentials.email}'")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user.role
        }

    @staticmethod
    def log_logout(
        db: Session, 
        user_id: int, 
        email: str, 
        ip_address: Optional[str] = None
    ) -> None:
        """
        Audits user logout event.
        """
        audit_log_repo.log_action(
            db,
            user_id=user_id,
            action="User Logout",
            details=f"User {email} logged out",
            ip_address=ip_address
        )
        audit_logger.info(f"AuthService: Logged logout event for user '{email}'")
