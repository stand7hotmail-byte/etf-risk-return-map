# -*- coding: utf-8 -*-
"""
Authentication service to handle user creation, authentication, and password hashing.
"""
from typing import Optional

from bcrypt import checkpw, gensalt, hashpw
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas import UserCreate, UserInDB


class AuthService:
    """
    Handles authentication-related operations such as user management and password security.
    """

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        Retrieves a user from the database by their username.

        Args:
            db: The database session.
            username: The username to search for.

        Returns:
            The User object if found, otherwise None.
        """
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """
        Creates a new user in the database.

        Args:
            db: The database session.
            user: The UserCreate schema containing username and password.

        Returns:
            The newly created User object.
        """
        hashed_password = AuthService.get_password_hash(user.password)
        # Check if this is the first user; if so, make them admin.
        is_admin = db.query(User).count() == 0
        
        db_user = User(
            username=user.username,
            hashed_password=hashed_password,
            is_admin=is_admin
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def create_user_from_google(db: Session, email: str) -> User:
        """
        Creates or retrieves a user authenticated via Google.

        Args:
            db: The database session.
            email: The user's email from Google.

        Returns:
            The User object.
        """
        user = AuthService.get_user_by_username(db, username=email)
        if user:
            return user
        
        # If user doesn't exist, create a new one with a dummy password
        # For Google OAuth, password is not used for direct login
        hashed_password = AuthService.get_password_hash("google_oauth_dummy_password")
        is_admin = db.query(User).count() == 0 # First user is admin
        
        db_user = User(
            username=email,
            hashed_password=hashed_password,
            is_admin=is_admin
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifies if a plain password matches a hashed password.

        Args:
            plain_password: The plain text password.
            hashed_password: The hashed password from the database.

        Returns:
            True if passwords match, False otherwise.
        """
        return checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Hashes a password using bcrypt.

        Args:
            password: The plain text password.

        Returns:
            The hashed password string.
        """
        pwd_bytes = password.encode('utf-8')
        salt = gensalt()
        hashed_bytes = hashpw(pwd_bytes, salt)
        return hashed_bytes.decode('utf-8')

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticates a user by username and password.

        Args:
            db: The database session.
            username: The user's username.
            password: The user's plain text password.

        Returns:
            The User object if authentication is successful, otherwise None.
        """
        user = AuthService.get_user_by_username(db, username)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user
