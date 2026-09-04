"""
Auth Router — handles user registration, login, and profile.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    """Request body for user registration."""
    full_name: str
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    """Request body for user login."""
    username: str
    password: str


class UserInfo(BaseModel):
    """User information in responses."""
    id: int
    full_name: str
    username: str
    email: str
    role: str
    is_active: bool


class LoginResponse(BaseModel):
    """Response body for successful login."""
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class RegisterResponse(BaseModel):
    """Response body for successful registration."""
    user: UserInfo
    message: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    summary="Register a new inspector",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_inspector(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new user as INSPECTOR.

    Public registration is only available for the INSPECTOR role.
    Admin users must be created through the controlled admin creation mechanism.
    """
    # Validate input
    if not request.full_name.strip():
        raise HTTPException(status_code=400, detail="Full name is required.")
    if not request.username.strip():
        raise HTTPException(status_code=400, detail="Username is required.")
    if not request.email.strip():
        raise HTTPException(status_code=400, detail="Email is required.")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    # Check uniqueness
    existing_user = db.query(User).filter(
        (User.username == request.username.strip()) | (User.email == request.email.strip())
    ).first()

    if existing_user:
        if existing_user.username == request.username.strip():
            raise HTTPException(status_code=409, detail="Username already taken.")
        raise HTTPException(status_code=409, detail="Email already registered.")

    # Create user (always INSPECTOR via public registration)
    user = User(
        full_name=request.full_name.strip(),
        username=request.username.strip(),
        email=request.email.strip(),
        password_hash=hash_password(request.password),
        role="INSPECTOR",
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(user)

    logger.info(f"New inspector registered: {user.username}")

    return RegisterResponse(
        user=UserInfo(
            id=user.id,
            full_name=user.full_name,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
        ),
        message="Registration successful.",
    )


@router.post(
    "/login",
    summary="Login with username and password",
    response_model=LoginResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and return a JWT access token.
    """
    # Find user by username
    user = db.query(User).filter(User.username == request.username).first()

    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})

    logger.info(f"User logged in: {user.username}")

    return LoginResponse(
        access_token=access_token,
        user=UserInfo(
            id=user.id,
            full_name=user.full_name,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
        ),
    )


@router.get(
    "/me",
    summary="Get current user profile",
    response_model=UserInfo,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """Return the authenticated user's profile information."""
    return UserInfo(
        id=current_user.id,
        full_name=current_user.full_name,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
    )
