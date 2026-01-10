"""
API Key Authentication Dependency

Security best practice: API key authentication for production.
When API_KEY is empty (default in development), authentication is skipped.
"""
from fastapi import Header, HTTPException, status
from app.core.config import settings


async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """
    Validates the API key from the X-API-Key header.
    
    If settings.API_KEY is empty (development mode), authentication is skipped.
    In production, set API_KEY in .env.production.
    """
    # Skip auth if no API key is configured (development mode)
    if not settings.API_KEY:
        return None
    
    # Require header if API key is configured
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Validate API key using constant-time comparison
    import secrets
    if not secrets.compare_digest(x_api_key, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    return x_api_key
