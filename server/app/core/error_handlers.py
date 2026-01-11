"""
Structured Error Handling for FastAPI.

Provides:
- Custom exception classes with error codes
- Global exception handlers
- Request correlation IDs
- User-friendly error messages
"""

import uuid
import time
from typing import Any, Dict, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded

from app.core.clients import get_logger

logger = get_logger(__name__)


# Error codes and their default messages
class ErrorCode:
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    NEO4J_UNAVAILABLE = "NEO4J_UNAVAILABLE"
    OPENSEARCH_UNAVAILABLE = "OPENSEARCH_UNAVAILABLE"
    QDRANT_UNAVAILABLE = "QDRANT_UNAVAILABLE"
    REDIS_UNAVAILABLE = "REDIS_UNAVAILABLE"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


# User-friendly messages
ERROR_MESSAGES = {
    ErrorCode.RATE_LIMIT_EXCEEDED: "Du hast zu viele Anfragen gesendet. Bitte warte einen Moment.",
    ErrorCode.SERVICE_UNAVAILABLE: "Der Dienst ist vorübergehend nicht verfügbar.",
    ErrorCode.LLM_TIMEOUT: "Die Antwortgenerierung hat zu lange gedauert.",
    ErrorCode.VALIDATION_ERROR: "Ungültige Eingabe. Bitte überprüfe deine Anfrage.",
    ErrorCode.RETRIEVAL_FAILED: "Die Dokumentensuche ist fehlgeschlagen.",
    ErrorCode.NEO4J_UNAVAILABLE: "Prozessdaten sind momentan nicht verfügbar.",
    ErrorCode.OPENSEARCH_UNAVAILABLE: "Die Volltextsuche ist momentan nicht verfügbar.",
    ErrorCode.QDRANT_UNAVAILABLE: "Die Vektorsuche ist momentan nicht verfügbar.",
    ErrorCode.REDIS_UNAVAILABLE: "Der Cache-Dienst ist momentan nicht verfügbar.",
    ErrorCode.UNKNOWN_ERROR: "Ein unerwarteter Fehler ist aufgetreten.",
}


class APIError(Exception):
    """Base exception for API errors with structured response."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.user_message = user_message or ERROR_MESSAGES.get(code, ERROR_MESSAGES[ErrorCode.UNKNOWN_ERROR])
        super().__init__(message)


class RateLimitError(APIError):
    """Rate limit exceeded error."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            status_code=429,
            details={"retry_after": retry_after},
            user_message=f"Du hast zu viele Anfragen gesendet. Bitte warte {retry_after} Sekunden.",
        )


class ServiceUnavailableError(APIError):
    """Service unavailable error."""

    def __init__(self, service: str, message: Optional[str] = None):
        code_map = {
            "neo4j": ErrorCode.NEO4J_UNAVAILABLE,
            "opensearch": ErrorCode.OPENSEARCH_UNAVAILABLE,
            "qdrant": ErrorCode.QDRANT_UNAVAILABLE,
            "redis": ErrorCode.REDIS_UNAVAILABLE,
            "ollama": ErrorCode.SERVICE_UNAVAILABLE,
        }
        error_code = code_map.get(service.lower(), ErrorCode.SERVICE_UNAVAILABLE)
        super().__init__(
            code=error_code,
            message=message or f"Service {service} is unavailable",
            status_code=503,
            details={"service": service},
        )


class LLMTimeoutError(APIError):
    """LLM generation timeout error."""

    def __init__(self, timeout_seconds: int = 120):
        super().__init__(
            code=ErrorCode.LLM_TIMEOUT,
            message=f"LLM generation timed out after {timeout_seconds} seconds",
            status_code=504,
            details={"timeout": timeout_seconds},
        )


class RetrievalError(APIError):
    """Document retrieval error."""

    def __init__(self, message: str, source: str = "unknown"):
        super().__init__(
            code=ErrorCode.RETRIEVAL_FAILED,
            message=message,
            status_code=500,
            details={"source": source},
        )


def build_error_response(
    code: str,
    message: str,
    request_id: str,
    details: Optional[Dict[str, Any]] = None,
    user_message: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a structured error response."""
    return {
        "error": {
            "code": code,
            "message": user_message or ERROR_MESSAGES.get(code, message),
            "details": details or {},
            "request_id": request_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    }


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle APIError exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    logger.error(
        "API error: code=%s, message=%s, request_id=%s",
        exc.code,
        exc.message,
        request_id,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            code=exc.code,
            message=exc.message,
            request_id=request_id,
            details=exc.details,
            user_message=exc.user_message,
        ),
    )


async def rate_limit_error_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handle rate limit exceeded errors with structured response."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Extract retry-after from the exception if available
    retry_after = 60  # Default
    if hasattr(exc, "detail") and isinstance(exc.detail, str):
        # Try to parse "Rate limit exceeded: X per minute" format
        import re
        match = re.search(r"(\d+)", exc.detail)
        if match:
            retry_after = 60  # Default to 1 minute for per-minute limits
    
    logger.warning(
        "Rate limit exceeded: request_id=%s, retry_after=%s",
        request_id,
        retry_after,
    )
    
    return JSONResponse(
        status_code=429,
        content=build_error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=str(exc.detail),
            request_id=request_id,
            details={"retry_after": retry_after},
            user_message=f"Du hast zu viele Anfragen gesendet. Bitte warte {retry_after} Sekunden.",
        ),
        headers={"Retry-After": str(retry_after)},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with structured response."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Map common HTTP status codes to error codes
    code_map = {
        400: ErrorCode.VALIDATION_ERROR,
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        422: ErrorCode.VALIDATION_ERROR,
        500: ErrorCode.UNKNOWN_ERROR,
        502: ErrorCode.SERVICE_UNAVAILABLE,
        503: ErrorCode.SERVICE_UNAVAILABLE,
        504: ErrorCode.LLM_TIMEOUT,
    }
    error_code = code_map.get(exc.status_code, ErrorCode.UNKNOWN_ERROR)
    
    logger.error(
        "HTTP exception: status=%s, detail=%s, request_id=%s",
        exc.status_code,
        exc.detail,
        request_id,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            code=error_code,
            message=str(exc.detail),
            request_id=request_id,
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions with structured response."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    logger.exception(
        "Unhandled exception: request_id=%s, error=%s",
        request_id,
        str(exc),
    )
    
    return JSONResponse(
        status_code=500,
        content=build_error_response(
            code=ErrorCode.UNKNOWN_ERROR,
            message="An internal server error occurred",
            request_id=request_id,
        ),
    )


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests."""

    async def dispatch(self, request: Request, call_next):
        # Generate or use existing request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        # Add timing
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log request timing
        duration = time.perf_counter() - start_time
        logger.info(
            "Request completed: method=%s, path=%s, status=%s, duration=%.3fs, request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration,
            request_id,
        )
        
        return response


def register_error_handlers(app):
    """Register all error handlers with the FastAPI app."""
    from slowapi.errors import RateLimitExceeded
    
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
