# -*- coding: utf-8 -*-
"""
API endpoints for user authentication (registration, login, Google OAuth).
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter # 追加
from slowapi.util import get_remote_address # 追加

from app.database import get_db
from app.dependencies import create_access_token # get_rate_limiterは不要になる
from app.schemas import Token, UserCreate
from app.services.auth_service import AuthService

# 各ルーターファイルで個別のLimiterインスタンスを定義
# このlimiterがデコレータで参照される
limiter = Limiter(key_func=get_remote_address)


router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=Token, summary="Register a new user")
@limiter.limit("3/minute") # レート制限を追加
async def register_user(
    request: Request,
    user_data: UserCreate, db: Session = Depends(get_db),
    # limiter: Limiter = Depends(get_rate_limiter) # ここは不要になる
):
    """
    Registers a new user with a username and password.

    Args:
        request: The FastAPI request object for rate limiting.
        user_data: The UserCreate schema containing username and password.
        db: The database session.
        # limiter: The rate limiter instance. # ここは不要になる

    Returns:
        A Token object containing the access token and token type.

    Raises:
        HTTPException: If the username already exists.
    """
    db_user = AuthService.get_user_by_username(db, username=user_data.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = AuthService.create_user(db, user_data)
    
    # Generate token for the newly registered user
    access_token_expires = timedelta(minutes=30) # Use the value from settings/env
    access_token = create_access_token(
        data={"sub": new_user.username, "is_admin": new_user.is_admin}, # is_adminを渡す
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=Token, summary="Authenticate user and get JWT token")
@limiter.limit("5/minute") # レート制限を追加
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db),
    # limiter: Limiter = Depends(get_rate_limiter) # ここは不要になる
):
    """
    Authenticates a user with username and password and returns a JWT access token.

    Args:
        request: The FastAPI request object for rate limiting.
        form_data: OAuth2PasswordRequestForm containing username and password.
        db: The database session.
        # limiter: The rate limiter instance. # ここは不要になる

    Returns:
        A Token object containing the access token and token type.

    Raises:
        HTTPException: If authentication fails.
    """
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30) # Use the value from settings/env
    access_token = create_access_token(
        data={"sub": user.username, "is_admin": user.is_admin}, # is_adminを渡す
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token/google", response_model=Token, summary="Authenticate with Google OAuth token")
@limiter.limit("10/minute") # レート制限を追加
async def login_with_google(
    request: Request,
    # Firebase Admin SDK is needed here to verify the ID token
    # For simplicity, this example assumes a valid ID token is provided
    # In a real app, you would verify this with firebase_admin.auth.verify_id_token
    google_token: dict, # Should be GoogleToken schema in schemas.py
    db: Session = Depends(get_db),
    # limiter: Limiter = Depends(get_rate_limiter) # ここは不要になる
):
    """
    Authenticates a user using a Google ID token and returns a JWT access token.

    Args:
        request: The FastAPI request object for rate limiting.
        google_token: A dictionary containing the Google ID token.
                      (Ideally should be GoogleToken schema).
        db: The database session.
        # limiter: The rate limiter instance. # ここは不要になる

    Returns:
        A Token object containing the access token and token type.

    Raises:
        HTTPException: If token verification fails or user is not found/created.
    """
    # Placeholder for actual Google ID token verification
    # In a real application, you would:
    # 1. Verify the Google ID token using Firebase Admin SDK or Google API client
    #    id_info = auth.verify_id_token(google_token.token)
    # 2. Extract user_id/email from id_info
    # 3. Look up or create user in your database
    # For now, let's mock a user based on a dummy Google token structure
    
    # Assuming google_token is actually the id_info from Firebase
    user_email = google_token.get("email", "google_user@example.com")
    
    user = AuthService.get_user_by_username(db, user_email)
    if not user:
        # Auto-provision user if not found
        user = AuthService.create_user_from_google(db, user_email)
        
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username, "is_admin": user.is_admin}, # is_adminを渡す
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
