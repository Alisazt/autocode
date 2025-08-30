"""
Authentication API endpoints.

This module exposes a small set of API endpoints for user authentication. It
relies on the `AuthService` defined in `backend/services/auth_service.py` to
perform the actual user verification and token generation. Endpoints include
login and a test endpoint to verify that a token is still valid.
"""

from fastapi import APIRouter, HTTPException, Depends
from ..services.auth_service import (
    auth_service,
    UserLogin,
    TokenResponse,
    User,
    get_current_user,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin) -> TokenResponse:
    """Authenticate a user and return an access and refresh token pair."""
    try:
        return auth_service.login(login_data)
    except HTTPException:
        # Pass through FastAPI HTTPExceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> User:
    """Return the current authenticated user's information."""
    return current_user


@router.get("/test-token")
async def test_token(current_user: User = Depends(get_current_user)) -> dict[str, str]:
    """Test endpoint to verify that a JWT token is valid."""
    return {"message": f"Hello {current_user.name}, your token is valid!"}