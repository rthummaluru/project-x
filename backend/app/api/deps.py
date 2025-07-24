# backend/app/api/deps.py
"""
FastAPI dependencies for authentication and common functionality.

Dependencies in FastAPI are functions that run before your endpoint handlers.
They're perfect for:
- Authentication and authorization
- Database session management
- Input validation
- Rate limiting

The Depends() function automatically calls these dependencies and injects
their return values into your endpoint functions.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import jwt
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User  # We'll need to create this model

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme for JWT authentication
security = HTTPBearer()

class CurrentUser:
    """
    Simple user model for dependency injection.
    
    This represents the currently authenticated user and provides
    the essential information needed for multi-tenant operations.
    """
    
    def __init__(self, id: int, email: str, company_id: int, is_active: bool = True):
        self.id = id
        self.email = email
        self.company_id = company_id  # Critical for multi-tenancy!
        self.is_active = is_active

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> CurrentUser:
    """
    Dependency that extracts and validates the current user from JWT token.
    
    This function:
    1. Extracts the JWT token from the Authorization header
    2. Validates the token signature and expiration
    3. Looks up the user in the database
    4. Returns a CurrentUser object with company_id for multi-tenancy
    
    **Multi-tenant Security:**
    The company_id is the key to data isolation. Every database query
    must filter by the current user's company_id.
    
    Args:
        credentials: JWT token from Authorization header
        db: Database session
        
    Returns:
        CurrentUser object with id, email, and company_id
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    
    # Define the exception for invalid credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=["HS256"]
        )
        
        # Extract user information from token
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # Check token expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Look up user in database
    # Note: In a real implementation, you'd query your User model here
    # For now, we'll create a mock user for development
    
    # TODO: Replace this with actual database query
    # Example:
    # user = await db.get(User, user_id)
    # if user is None or not user.is_active:
    #     raise credentials_exception
    
    # Mock user for development (REMOVE THIS IN PRODUCTION!)
    current_user = CurrentUser(
        id=user_id,
        email="demo@example.com",
        company_id=1,  # In real app, this comes from database
        is_active=True
    )
    
    return current_user

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.
    
    This utility function creates JWT tokens for user authentication.
    You'll use this in your login endpoint.
    
    Args:
        data: Dictionary containing user information to encode
        
    Returns:
        Encoded JWT token string
        
    Example usage:
        token = create_access_token({"sub": user.id, "email": user.email})
    """
    
    to_encode = data.copy()
    
    # Set token expiration
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    
    # Encode the token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm="HS256"
    )
    
    return encoded_jwt

async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Dependency that ensures the current user is active.
    
    Use this instead of get_current_user when you want to ensure
    the user account is active and not disabled.
    """
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user

# Optional: Admin-only dependency
async def get_admin_user(
    current_user: CurrentUser = Depends(get_current_active_user)
) -> CurrentUser:
    """
    Dependency that ensures the current user has admin privileges.
    
    Example usage:
    @router.delete("/companies/{company_id}")
    async def delete_company(admin: CurrentUser = Depends(get_admin_user)):
        # Only admins can access this endpoint
    """
    
    # TODO: Add admin role checking
    # In a real app, you'd check user.role == "admin" or similar
    
    return current_user

# Rate limiting dependency (basic version)
class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    For production, you'd use Redis or a proper rate limiting service.
    This is just for demonstration.
    """
    
    def __init__(self, max_requests: int = 100, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests = {}  # In production, use Redis
    
    async def __call__(
        self,
        current_user: CurrentUser = Depends(get_current_user)
    ) -> CurrentUser:
        """Check rate limit for current user."""
        
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # Clean old requests
        user_requests = self.requests.get(current_user.id, [])
        user_requests = [req_time for req_time in user_requests if req_time > window_start]
        
        # Check limit
        if len(user_requests) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.max_requests} requests per {self.window_minutes} minutes"
            )
        
        # Add current request
        user_requests.append(now)
        self.requests[current_user.id] = user_requests
        
        return current_user

# Create rate limiter instance
rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_per_minute,
    window_minutes=1
)