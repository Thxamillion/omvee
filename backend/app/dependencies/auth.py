from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.auth.jwks_verifier import get_jwks_verifier, JWKSError, AuthClaims

logger = logging.getLogger(__name__)

# HTTP Bearer scheme for extracting JWT tokens from Authorization header
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> str:
    """
    FastAPI dependency to extract and verify JWT token, returning user_id.

    This is the main auth dependency for protected endpoints.
    Raises HTTP 401 if token is missing or invalid.

    Returns:
        str: The user_id (UUID) from the token's 'sub' claim

    Raises:
        HTTPException: 401 if authentication fails
    """
    if not credentials:
        logger.warning("No authorization header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    if not token:
        logger.warning("Empty token in authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        verifier = get_jwks_verifier()
        claims = await verifier.verify_token(token)

        logger.debug(f"Authenticated user: {claims.user_id}")
        return claims.user_id

    except JWKSError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error in auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_current_user_claims(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> AuthClaims:
    """
    FastAPI dependency to extract and verify JWT token, returning full claims.

    Use this when you need access to additional claims beyond just user_id
    (like email, role, etc.).

    Returns:
        AuthClaims: Full validated claims from the JWT

    Raises:
        HTTPException: 401 if authentication fails
    """
    if not credentials:
        logger.warning("No authorization header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    if not token:
        logger.warning("Empty token in authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        verifier = get_jwks_verifier()
        claims = await verifier.verify_token(token)

        logger.debug(f"Authenticated user with claims: {claims.user_id}")
        return claims

    except JWKSError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error in auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> Optional[str]:
    """
    FastAPI dependency for optional authentication.

    Returns user_id if valid token is provided, None otherwise.
    Does not raise exceptions for missing/invalid tokens.

    Useful for endpoints that work for both authenticated and anonymous users.

    Returns:
        Optional[str]: user_id if authenticated, None if not
    """
    if not credentials or not credentials.credentials:
        logger.debug("No credentials provided for optional auth")
        return None

    try:
        verifier = get_jwks_verifier()
        claims = await verifier.verify_token_optional(credentials.credentials)

        if claims:
            logger.debug(f"Optional auth successful for user: {claims.user_id}")
            return claims.user_id
        else:
            logger.debug("Optional auth failed, proceeding as anonymous")
            return None

    except Exception as e:
        logger.warning(f"Error in optional auth (proceeding as anonymous): {e}")
        return None


async def get_optional_user_claims(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> Optional[AuthClaims]:
    """
    FastAPI dependency for optional authentication with full claims.

    Returns AuthClaims if valid token is provided, None otherwise.
    Does not raise exceptions for missing/invalid tokens.

    Returns:
        Optional[AuthClaims]: Full claims if authenticated, None if not
    """
    if not credentials or not credentials.credentials:
        logger.debug("No credentials provided for optional auth")
        return None

    try:
        verifier = get_jwks_verifier()
        claims = await verifier.verify_token_optional(credentials.credentials)

        if claims:
            logger.debug(f"Optional auth successful for user: {claims.user_id}")
            return claims
        else:
            logger.debug("Optional auth failed, proceeding as anonymous")
            return None

    except Exception as e:
        logger.warning(f"Error in optional auth (proceeding as anonymous): {e}")
        return None


def require_role(required_role: str):
    """
    FastAPI dependency factory for role-based access control.

    Args:
        required_role: The role required to access the endpoint

    Returns:
        FastAPI dependency function that checks user role

    Example:
        @app.get("/admin/users", dependencies=[Depends(require_role("admin"))])
        async def list_admin_users():
            pass
    """
    async def role_dependency(
        claims: AuthClaims = Depends(get_current_user_claims)
    ) -> AuthClaims:
        if claims.role != required_role:
            logger.warning(f"Access denied: user {claims.user_id} has role '{claims.role}', requires '{required_role}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role"
            )
        return claims

    return role_dependency


# Common role dependencies for convenience
require_admin = require_role("admin")
require_service_role = require_role("service_role")