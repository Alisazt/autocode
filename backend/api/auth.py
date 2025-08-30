"""
Authentication API routes for the demo AutoDev project.

This router provides endpoints for user registration, login,
token refresh, logout, and fetching the current user's information.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from ..services.auth_service import (
    auth_service,
    UserCreate,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    User,
    get_current_active_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=User)
async def register(user_data: UserCreate):
    """Register a new user."""
    try:
        return auth_service.create_user(user_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {e}")


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Login a user and return access and refresh tokens."""
    try:
        return auth_service.login(login_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Login failed: {e}")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh an access token using a refresh token."""
    token_response = auth_service.refresh_access_token(request.refresh_token)
    if not token_response:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    return token_response


@router.post("/logout")
async def logout(request: RefreshTokenRequest):
    """Invalidate a refresh token to log out a user."""
    success = auth_service.logout(request.refresh_token)
    return {"message": "Logged out successfully" if success else "Token not found"}


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get the currently authenticated user."""
    return current_user
