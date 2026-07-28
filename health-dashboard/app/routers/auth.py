"""
Router defining authentication API endpoints.
"""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services.auth import AuthService

logger = logging.getLogger("app")
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post(
    "/login", 
    response_model=schemas.Token,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates admin credentials and returns a JWT access token."
)
def login(
    user_credentials: schemas.UserCreate, 
    db: Session = Depends(get_db)
) -> dict:
    """
    Log in a user.

    Logs the login attempt and calls the authentication service.
    """
    logger.info(f"POST /api/auth/login - Login request received for user: '{user_credentials.username}'")
    return AuthService.authenticate_user(db, user_credentials)
