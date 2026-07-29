"""
FastAPI dependencies for database sessions, authentication, and RBAC roles check.
"""

from typing import Generator, List, Optional
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.database.models import User
from app.core import security
from app.repositories.user import user_repo

def get_db() -> Generator[Session, None, None]:
    """
    Dependency yielding database sessions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_token_from_request(request: Request) -> Optional[str]:
    """
    Helper to extract JWT tokens from either HTTP headers or cookies.
    Allows authentication for both API fetches and direct Jinja2 page navigations.
    """
    # 1. Check Authorization Header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    
    # 2. Check Cookie (e.g. for HTML page loads)
    return request.cookies.get("access_token")

def get_current_user_optional(
    request: Request, 
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency that retrieves the current user if authenticated, returning None otherwise.
    Does not raise exceptions (useful for optional pages).
    """
    token = get_token_from_request(request)
    if not token:
        return None
        
    payload = security.decode_access_token(token)
    if not payload:
        return None
        
    email = payload.get("sub")
    if not email:
        return None
        
    return user_repo.get_by_email(db, email)

def get_current_user(
    request: Request, 
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency requiring valid JWT authentication. Raises 401 if unauthorized.
    """
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication session has expired or is invalid. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

class RoleChecker:
    """
    Role-Based Access Control validator dependency.
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role level: {', '.join(self.allowed_roles)}."
            )
        return current_user

# Pre-defined Role dependencies
require_admin = RoleChecker(["Admin"])
require_operator = RoleChecker(["Admin", "Operator"])
require_viewer = RoleChecker(["Admin", "Operator", "Viewer"])
