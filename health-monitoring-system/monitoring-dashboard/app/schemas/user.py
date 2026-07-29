"""
Pydantic schemas for user registration, login, and profile serializations.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator, model_validator

class UserBase(BaseModel):
    """
    Base user schema containing generic user profile properties.
    """
    first_name: str = Field(..., min_length=1, max_length=50, description="User first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="User last name")
    email: EmailStr = Field(..., description="Unique email address")

class UserRegister(UserBase):
    """
    Schema for registering a new user account with strong password requirements.
    """
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    confirm_password: str = Field(..., description="Confirm password confirmation entry")
    role: Optional[str] = Field("Viewer", pattern="^(Admin|Operator|Viewer)$", description="Assigned authorization role")

    @field_validator("password")
    @classmethod
    def validate_strong_password(cls, v: str) -> str:
        """
        Validates that password meets complexity rules:
        - At least 8 characters
        - Contains at least 1 uppercase letter
        - Contains at least 1 lowercase letter
        - Contains at least 1 number
        - Contains at least 1 special character
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase character.")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase character.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number.")
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?~`"
        if not any(c in special_chars for c in v):
            raise ValueError("Password must contain at least one special character (e.g. !@#$%).")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "UserRegister":
        """
        Verifies that both password and confirmation entries are identical.
        """
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self

class UserLogin(BaseModel):
    """
    Schema representing user login credentials.
    """
    email: EmailStr = Field(..., description="User account email")
    password: str = Field(..., description="User password")

class UserResponse(UserBase):
    """
    Output schema representing user profiles.
    """
    id: int
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    """
    Output schema containing JWT tokens returned on successful login.
    """
    access_token: str
    token_type: str
    role: str

class TokenData(BaseModel):
    """
    Internal model detailing validated token data payloads.
    """
    email: Optional[str] = None
    role: Optional[str] = None
