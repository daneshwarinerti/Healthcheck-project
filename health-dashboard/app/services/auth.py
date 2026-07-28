"""
Auth service layer handling administrator verification and JWT token generation.
"""

import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app import models, schemas, auth

logger = logging.getLogger("app")

class AuthService:
    """
    Service class encapsulating authentication operations.
    """

    @staticmethod
    def authenticate_user(db: Session, user_credentials: schemas.UserCreate) -> dict:
        """
        Authenticates admin user credentials and returns a JWT access token.

        Args:
            db (Session): Database transaction session.
            user_credentials (UserCreate): Schema containing username and password.

        Raises:
            HTTPException: 401 Unauthorized if verification fails.

        Returns:
            dict: The JWT access token container.
        """
        logger.info(f"AuthService: Checking login credentials for user: '{user_credentials.username}'")
        
        # Look up user in database
        user = db.query(models.User).filter(
            models.User.username == user_credentials.username
        ).first()
        
        # Verify credentials
        if not user or not auth.verify_password(user_credentials.password, user.hashed_password):
            logger.warning(f"AuthService: Login failure for user: '{user_credentials.username}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Create token
        access_token = auth.create_access_token(data={"sub": user.username})
        logger.info(f"AuthService: Login success for user: '{user_credentials.username}'")
        
        return {
            "access_token": access_token, 
            "token_type": "bearer"
        }
