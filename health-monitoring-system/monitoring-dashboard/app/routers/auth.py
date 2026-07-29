"""
Router defining authentication API and page routes.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import schemas
from app.dependencies import get_db, get_current_user_optional
from app.services.auth_service import AuthService

logger = logging.getLogger("app")
router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="app/templates")

# ----------------------------------------------------
# Page Rendering Routes (HTML)
# ----------------------------------------------------

@router.get("/login", response_class=HTMLResponse)
def render_login(request: Request, current_user = Depends(get_current_user_optional)):
    """
    Renders the Administrator/Operator authentication portal login view.
    Redirects to dashboard if already authenticated.
    """
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("login.html", {"request": request, "app_name": "SRE Monitoring"})

@router.get("/register", response_class=HTMLResponse)
def render_register(request: Request, current_user = Depends(get_current_user_optional)):
    """
    Renders the sign-up page. Redirects to dashboard if already authenticated.
    """
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("register.html", {"request": request, "app_name": "SRE Monitoring"})

@router.get("/logout")
def logout(response: Response, request: Request, db: Session = Depends(get_db), current_user = Depends(get_current_user_optional)):
    """
    Clears the session authorization cookies and redirects the user to the login viewport.
    """
    redirect_res = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    redirect_res.delete_cookie("access_token")
    
    if current_user:
        # Audit log logout
        AuthService.log_logout(
            db, 
            user_id=current_user.id, 
            email=current_user.email, 
            ip_address=request.client.host if request.client else "127.0.0.1"
        )
    return redirect_res

# ----------------------------------------------------
# REST API Endpoints (JSON)
# ----------------------------------------------------

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_api(
    user_in: schemas.UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Registers a new operator/admin account. Prevents duplicate registrations.
    """
    ip = request.client.host if request.client else "127.0.0.1"
    return AuthService.register_user(db, user_in, ip_address=ip)

@router.post("/login", response_model=schemas.Token)
def login_api(
    response: Response,
    credentials: schemas.UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Verifies credentials, issues a JWT, and sets it inside an access cookie.
    """
    ip = request.client.host if request.client else "127.0.0.1"
    auth_data = AuthService.authenticate_user(db, credentials, ip_address=ip)
    
    # Store token inside cookie to support native Jinja2 page loading authentication
    response.set_cookie(
        key="access_token",
        value=auth_data["access_token"],
        httponly=True,
        max_age=7200,  # 2 hours
        samesite="lax"
    )
    return auth_data
