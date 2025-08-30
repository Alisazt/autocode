"""
Basic authentication service for CrewAI AutoDev.
"""

from __future__ import annotations
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# NOTE: In production you should load the secret key from environment variables or a secret manager.
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class UserCreate(BaseModel):
    email: str
    password: str
    name: str


class UserLogin(BaseModel):
    email: str
    password: str


class User(BaseModel):
    id: str
    email: str
    name: str
    created_at: str
    is_active: bool = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthService:
    """
    Simple in-memory authentication service. Provides methods for user registration,
    login and token verification. This implementation stores user data and refresh
    tokens in memory and is not persistent. In production, replace this with a
    persistent store and proper password hashing.
    """

    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.refresh_tokens: Dict[str, str] = {}
        self._create_default_user()

    def _create_default_user(self) -> None:
        """Create a default admin user for demo purposes."""
        user_id = "admin-123"
        self.users[user_id] = {
            "id": user_id,
            "email": "admin@crewai.dev",
            "name": "Admin User",
            "password_hash": self._hash_password("admin123"),
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }

    def _hash_password(self, password: str) -> str:
        """Hash a plaintext password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a plaintext password against its hash."""
        return self._hash_password(password) == password_hash

    def create_access_token(self, user_id: str) -> str:
        """Create a JWT access token for the given user id."""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": user_id, "exp": expire, "type": "access"}
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    def verify_access_token(self, token: str) -> Optional[User]:
        """Verify a JWT access token and return the user if valid."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")

            if user_id and user_id in self.users:
                user_data = self.users[user_id]
                if user_data["is_active"]:
                    # Return a User without the password_hash field
                    return User(**{k: v for k, v in user_data.items() if k != "password_hash"})
        except jwt.PyJWTError:
            return None
        return None

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        for user_data in self.users.values():
            if user_data["email"] == email and user_data["is_active"]:
                if self._verify_password(password, user_data["password_hash"]):
                    return User(**{k: v for k, v in user_data.items() if k != "password_hash"})
        return None

    def login(self, login_data: UserLogin) -> TokenResponse:
        """Authenticate user and return access/refresh tokens or raise 401."""
        user = self.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        access_token = self.create_access_token(user.id)
        refresh_token = secrets.token_urlsafe(32)
        self.refresh_tokens[refresh_token] = user.id

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )


# Instantiate a global auth service and security scheme for dependency injection.
auth_service = AuthService()
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """FastAPI dependency to get the current authenticated user or raise 401."""
    user = auth_service.verify_access_token(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user