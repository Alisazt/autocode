"""
Basic authentication service for the demo AutoDev project.

This module implements a simple in-memory user store with JWT-based
authentication. In production, you would replace this with a proper
identity provider and database-backed storage.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from pydantic import BaseModel


# Token configuration – in a real deployment, use JWTs and environment variables
# For the demo we implement simple random tokens with expiry tracking.
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class UserCreate(BaseModel):
    """Payload for registering a new user."""
    email: str
    password: str
    name: str


class UserLogin(BaseModel):
    """Payload for logging in a user."""
    email: str
    password: str


class User(BaseModel):
    """Public user model returned from the API."""
    id: str
    email: str
    name: str
    created_at: str
    is_active: bool = True


class TokenResponse(BaseModel):
    """Response model for access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Request model for refreshing an access token."""
    refresh_token: str


class AuthService:
    """Simple auth service with in-memory storage."""

    def __init__(self) -> None:
        self.users: Dict[str, Dict[str, Any]] = {}
        # Map refresh token to user ID
        self.refresh_tokens: Dict[str, str] = {}
        # Map access token to (user ID, expiry timestamp)
        self.access_tokens: Dict[str, float] = {}
        self._create_default_user()

    def _create_default_user(self) -> None:
        """Create a default admin user for testing."""
        user_id = "admin-123"
        self.users[user_id] = {
            "id": user_id,
            "email": "admin@autodev.local",
            "name": "Admin",
            "password_hash": self._hash_password("admin123"),
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
        }

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        return self._hash_password(password) == password_hash

    def _generate_user_id(self) -> str:
        return f"user-{secrets.token_urlsafe(8)}"

    def create_user(self, user_data: UserCreate) -> User:
        """Register a new user."""
        for user in self.users.values():
            if user["email"] == user_data.email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        user_id = self._generate_user_id()
        self.users[user_id] = {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "password_hash": self._hash_password(user_data.password),
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
        }
        user_record = self.users[user_id]
        return User(**{k: v for k, v in user_record.items() if k != "password_hash"})

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        for user in self.users.values():
            if user["email"] == email and user["is_active"]:
                if self._verify_password(password, user["password_hash"]):
                    return User(**{k: v for k, v in user.items() if k != "password_hash"})
        return None

    def create_access_token(self, user_id: str) -> str:
        """Generate a new access token for the given user.

        The token is a random string mapped to the user ID with an
        expiry timestamp. When verifying the token we consult the
        internal mapping to ensure it is valid and not expired.
        """
        token = secrets.token_urlsafe(32)
        expiry_ts = (datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
        self.access_tokens[token] = (user_id, expiry_ts)
        return token

    def create_refresh_token(self, user_id: str) -> str:
        token = secrets.token_urlsafe(32)
        self.refresh_tokens[token] = user_id
        return token

    def refresh_access_token(self, refresh_token: str) -> Optional[TokenResponse]:
        """Refresh an access token given a valid refresh token.

        Returns a new access token and refresh token or None if the refresh token
        is invalid.
        """
        if refresh_token not in self.refresh_tokens:
            return None
        user_id = self.refresh_tokens.pop(refresh_token)
        # Validate user
        if user_id not in self.users or not self.users[user_id]["is_active"]:
            return None
        # Generate new tokens
        access_token = self.create_access_token(user_id)
        new_refresh = self.create_refresh_token(user_id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def login(self, login_data: UserLogin) -> TokenResponse:
        user = self.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        access_token = self.create_access_token(user.id)
        refresh_token = self.create_refresh_token(user.id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def logout(self, refresh_token: str) -> bool:
        """Invalidate a refresh token to log out a user."""
        return bool(self.refresh_tokens.pop(refresh_token, None))

    def verify_access_token(self, token: str) -> Optional[User]:
        """Verify an access token and return the associated user if valid.

        For the demo we look up the token in the internal mapping and
        check expiry. Returns None if invalid or expired.
        """
        expiry_info = self.access_tokens.get(token)
        if not expiry_info:
            return None
        user_id, expiry_ts = expiry_info
        if datetime.utcnow().timestamp() > expiry_ts:
            # Token expired; remove from store
            self.access_tokens.pop(token, None)
            return None
        user = self.users.get(user_id)
        if not user or not user["is_active"]:
            return None
        return User(**{k: v for k, v in user.items() if k != "password_hash"})


# Instantiate a global auth service instance for injection
auth_service = AuthService()


def get_current_active_user(token: str) -> User:
    """Dependency to extract the currently authenticated user from a JWT token.

    In FastAPI this would typically be used with `Depends` and an HTTPBearer
    authentication scheme. For this demo, it is a simple function expecting
    the raw token as a parameter.
    """
    user = auth_service.verify_access_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user
