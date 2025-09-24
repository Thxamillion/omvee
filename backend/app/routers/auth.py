from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr
import logging

from app.services.supabase import get_supabase_client
from app.dependencies.auth import get_current_user_claims, AuthClaims
from supabase import Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models for request/response
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    metadata: Optional[Dict[str, Any]] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    token: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class UpdatePasswordRequest(BaseModel):
    new_password: str


class AuthResponse(BaseModel):
    user: Dict[str, Any]
    session: Dict[str, Any]
    message: str


class UserResponse(BaseModel):
    user: Dict[str, Any]


class MessageResponse(BaseModel):
    message: str


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: SignupRequest,
    supabase: Client = Depends(get_supabase_client)
) -> AuthResponse:
    """
    Create a new user account with email and password.

    Args:
        signup_data: User registration information

    Returns:
        AuthResponse: User data and session information

    Raises:
        HTTPException: If signup fails
    """
    try:
        logger.info(f"Creating new user account for: {signup_data.email}")

        response = supabase.auth.sign_up({
            "email": signup_data.email,
            "password": signup_data.password,
            "options": {
                "data": signup_data.metadata or {}
            }
        })

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )

        logger.info(f"User created successfully: {response.user.id}")

        return AuthResponse(
            user=response.user.model_dump(),
            session=response.session.model_dump() if response.session else {},
            message="Account created successfully. Please check your email for verification."
        )

    except Exception as e:
        logger.error(f"Signup error for {signup_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create account: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    supabase: Client = Depends(get_supabase_client)
) -> AuthResponse:
    """
    Authenticate user with email and password.

    Args:
        login_data: User login credentials

    Returns:
        AuthResponse: User data and session with access/refresh tokens

    Raises:
        HTTPException: If login fails
    """
    try:
        logger.info(f"Login attempt for: {login_data.email}")

        response = supabase.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password
        })

        if response.user is None or response.session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        logger.info(f"Login successful for user: {response.user.id}")

        return AuthResponse(
            user=response.user.model_dump(),
            session=response.session.model_dump(),
            message="Login successful"
        )

    except Exception as e:
        logger.warning(f"Login failed for {login_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    claims: AuthClaims = Depends(get_current_user_claims),
    supabase: Client = Depends(get_supabase_client)
) -> MessageResponse:
    """
    Logout the current user and invalidate their session.

    Args:
        claims: Current user claims from JWT token

    Returns:
        MessageResponse: Logout confirmation

    Raises:
        HTTPException: If logout fails
    """
    try:
        logger.info(f"Logout request for user: {claims.user_id}")

        # Sign out the user (invalidates the session)
        supabase.auth.sign_out()

        logger.info(f"User logged out successfully: {claims.user_id}")

        return MessageResponse(message="Logged out successfully")

    except Exception as e:
        logger.error(f"Logout error for user {claims.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout"
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    supabase: Client = Depends(get_supabase_client)
) -> AuthResponse:
    """
    Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token data

    Returns:
        AuthResponse: New user session with fresh tokens

    Raises:
        HTTPException: If refresh fails
    """
    try:
        logger.debug("Token refresh request")

        response = supabase.auth.refresh_session(refresh_data.refresh_token)

        if response.user is None or response.session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        logger.debug(f"Token refreshed for user: {response.user.id}")

        return AuthResponse(
            user=response.user.model_dump(),
            session=response.session.model_dump(),
            message="Token refreshed successfully"
        )

    except Exception as e:
        logger.warning(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


@router.get("/user", response_model=UserResponse)
async def get_current_user_info(
    claims: AuthClaims = Depends(get_current_user_claims),
    supabase: Client = Depends(get_supabase_client)
) -> UserResponse:
    """
    Get current user information.

    Args:
        claims: Current user claims from JWT token

    Returns:
        UserResponse: Current user data

    Raises:
        HTTPException: If user data retrieval fails
    """
    try:
        logger.debug(f"User info request for: {claims.user_id}")

        # Get user from Supabase (this validates the session is still active)
        response = supabase.auth.get_user()

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User session invalid"
            )

        return UserResponse(user=response.user.model_dump())

    except Exception as e:
        logger.error(f"Get user info error for {claims.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verify_data: VerifyEmailRequest,
    supabase: Client = Depends(get_supabase_client)
) -> MessageResponse:
    """
    Verify user email address with token.

    Args:
        verify_data: Email verification data

    Returns:
        MessageResponse: Verification confirmation

    Raises:
        HTTPException: If verification fails
    """
    try:
        logger.info(f"Email verification for: {verify_data.email}")

        response = supabase.auth.verify_otp({
            "email": verify_data.email,
            "token": verify_data.token,
            "type": "email"
        })

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )

        logger.info(f"Email verified successfully for: {verify_data.email}")

        return MessageResponse(message="Email verified successfully")

    except Exception as e:
        logger.error(f"Email verification failed for {verify_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification failed"
        )


@router.post("/reset-password", response_model=MessageResponse)
async def request_password_reset(
    reset_data: ResetPasswordRequest,
    supabase: Client = Depends(get_supabase_client)
) -> MessageResponse:
    """
    Request password reset email.

    Args:
        reset_data: Password reset request data

    Returns:
        MessageResponse: Reset email confirmation

    Raises:
        HTTPException: If request fails
    """
    try:
        logger.info(f"Password reset request for: {reset_data.email}")

        supabase.auth.reset_password_email(reset_data.email)

        logger.info(f"Password reset email sent to: {reset_data.email}")

        return MessageResponse(
            message="Password reset email sent. Please check your inbox."
        )

    except Exception as e:
        logger.error(f"Password reset request failed for {reset_data.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email"
        )


@router.post("/update-password", response_model=MessageResponse)
async def update_password(
    password_data: UpdatePasswordRequest,
    claims: AuthClaims = Depends(get_current_user_claims),
    supabase: Client = Depends(get_supabase_client)
) -> MessageResponse:
    """
    Update user password (requires authentication).

    Args:
        password_data: New password data
        claims: Current user claims from JWT token

    Returns:
        MessageResponse: Password update confirmation

    Raises:
        HTTPException: If update fails
    """
    try:
        logger.info(f"Password update request for user: {claims.user_id}")

        response = supabase.auth.update_user({
            "password": password_data.new_password
        })

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update password"
            )

        logger.info(f"Password updated successfully for user: {claims.user_id}")

        return MessageResponse(message="Password updated successfully")

    except Exception as e:
        logger.error(f"Password update failed for user {claims.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )


@router.get("/health")
async def auth_health() -> Dict[str, str]:
    """
    Health check endpoint for authentication service.
    Does not require authentication.
    """
    return {"status": "healthy", "service": "authentication"}