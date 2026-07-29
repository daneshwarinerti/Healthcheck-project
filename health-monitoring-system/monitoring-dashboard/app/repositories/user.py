"""
Repository class managing user data database operations.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.database.models import User
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    """
    User database repository interface.
    """

    def __init__(self):
        super().__init__(User)

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Retrieves a user record matching the given email address.
        """
        return db.query(self.model).filter(self.model.email == email).first()

# Global instance for injection
user_repo = UserRepository()
