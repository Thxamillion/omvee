import jwt
import httpx
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class JWKSError(Exception):
    """Custom exception for JWKS-related errors."""
    pass


class AuthClaims(BaseModel):
    """Validated JWT claims from Supabase auth token."""
    user_id: str  # 'sub' claim
    email: Optional[str] = None
    role: str = "authenticated"
    aud: str = "authenticated"
    exp: int
    iat: int
    iss: str


class SupabaseJWKSVerifier:
    """
    Verifies Supabase JWT tokens using JWKS (JSON Web Key Set).

    This uses asymmetric key cryptography (public/private keys) which is
    more secure than symmetric JWT secrets. Supabase provides public keys
    via their JWKS endpoint for token verification.
    """

    def __init__(self, supabase_url: str):
        self.supabase_url = supabase_url.rstrip('/')
        self.jwks_url = f"{self.supabase_url}/auth/v1/.well-known/jwks.json"
        self.issuer = f"{self.supabase_url}/auth/v1"

        # Cache JWKS to avoid repeated network calls
        self._jwks_cache: Optional[Dict] = None
        self._cache_expiry: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=10)  # Match Supabase Edge cache

        logger.info(f"Initialized JWKS verifier for {self.supabase_url}")

    async def _fetch_jwks(self) -> Dict:
        """Fetch JWKS from Supabase endpoint with error handling."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.debug(f"Fetching JWKS from {self.jwks_url}")
                response = await client.get(self.jwks_url)
                response.raise_for_status()

                jwks_data = response.json()
                logger.debug(f"Successfully fetched JWKS with {len(jwks_data.get('keys', []))} keys")
                return jwks_data

        except httpx.RequestError as e:
            logger.error(f"Network error fetching JWKS: {e}")
            raise JWKSError(f"Failed to fetch JWKS from {self.jwks_url}: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching JWKS: {e.response.status_code}")
            raise JWKSError(f"JWKS endpoint returned {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error fetching JWKS: {e}")
            raise JWKSError(f"Failed to parse JWKS response: {e}")

    async def get_jwks(self) -> Dict:
        """Get JWKS with caching to avoid repeated requests."""
        now = datetime.utcnow()

        # Return cached JWKS if still valid
        if (self._jwks_cache is not None and
            self._cache_expiry is not None and
            now < self._cache_expiry):
            logger.debug("Using cached JWKS")
            return self._jwks_cache

        # Fetch fresh JWKS
        self._jwks_cache = await self._fetch_jwks()
        self._cache_expiry = now + self._cache_ttl

        return self._jwks_cache

    def _construct_rsa_key(self, jwk: Dict) -> Any:
        """Construct RSA public key from JWK for PyJWT verification."""
        try:
            from jwt.algorithms import RSAAlgorithm
            return RSAAlgorithm.from_jwk(jwk)
        except Exception as e:
            logger.error(f"Failed to construct RSA key from JWK: {e}")
            raise JWKSError(f"Invalid RSA key in JWKS: {e}")

    def _construct_ec_key(self, jwk: Dict) -> Any:
        """Construct EC public key from JWK for PyJWT verification."""
        try:
            from jwt.algorithms import ECAlgorithm
            return ECAlgorithm.from_jwk(jwk)
        except Exception as e:
            logger.error(f"Failed to construct EC key from JWK: {e}")
            raise JWKSError(f"Invalid EC key in JWKS: {e}")

    def _find_key_for_token(self, token_header: Dict, jwks: Dict) -> Any:
        """Find the correct public key from JWKS for token verification."""
        kid = token_header.get("kid")
        if not kid:
            raise JWKSError("Token missing 'kid' (key ID) in header")

        # Find matching key in JWKS
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                kty = jwk.get("kty")

                if kty == "RSA":
                    return self._construct_rsa_key(jwk)
                elif kty == "EC":
                    return self._construct_ec_key(jwk)
                else:
                    raise JWKSError(f"Unsupported key type: {kty}")

        raise JWKSError(f"No matching key found for kid: {kid}")

    async def verify_token(self, token: str) -> AuthClaims:
        """
        Verify JWT token using JWKS and return validated claims.

        Args:
            token: JWT token string (without 'Bearer ' prefix)

        Returns:
            AuthClaims: Validated and parsed claims

        Raises:
            JWKSError: If verification fails for any reason
        """
        try:
            # Decode header without verification to get key ID
            token_header = jwt.get_unverified_header(token)
            logger.debug(f"Token header: {token_header}")

            # Get JWKS and find matching key
            jwks = await self.get_jwks()
            public_key = self._find_key_for_token(token_header, jwks)

            # Determine algorithm
            alg = token_header.get("alg")
            if alg not in ["RS256", "ES256", "RS384", "ES384", "RS512", "ES512"]:
                raise JWKSError(f"Unsupported algorithm: {alg}")

            # Verify token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[alg],
                audience="authenticated",
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "require": ["sub", "exp", "iat", "aud", "iss"]
                }
            )

            logger.debug(f"Token verified successfully for user: {payload.get('sub')}")

            # Return validated claims
            return AuthClaims(
                user_id=payload["sub"],
                email=payload.get("email"),
                role=payload.get("role", "authenticated"),
                aud=payload["aud"],
                exp=payload["exp"],
                iat=payload["iat"],
                iss=payload["iss"]
            )

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise JWKSError("Token has expired")
        except jwt.InvalidAudienceError:
            logger.warning("Invalid token audience")
            raise JWKSError("Invalid token audience")
        except jwt.InvalidIssuerError:
            logger.warning("Invalid token issuer")
            raise JWKSError("Invalid token issuer")
        except jwt.InvalidSignatureError:
            logger.warning("Invalid token signature")
            raise JWKSError("Invalid token signature")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise JWKSError(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"Unexpected error verifying token: {e}")
            raise JWKSError(f"Token verification failed: {e}")

    async def verify_token_optional(self, token: Optional[str]) -> Optional[AuthClaims]:
        """
        Verify token but return None if invalid instead of raising exception.
        Useful for optional authentication endpoints.
        """
        if not token:
            return None

        try:
            return await self.verify_token(token)
        except JWKSError:
            logger.debug("Optional token verification failed")
            return None


# Global verifier instance (initialized in main.py)
_jwks_verifier: Optional[SupabaseJWKSVerifier] = None


def initialize_jwks_verifier(supabase_url: str) -> None:
    """Initialize the global JWKS verifier instance."""
    global _jwks_verifier
    _jwks_verifier = SupabaseJWKSVerifier(supabase_url)
    logger.info("JWKS verifier initialized")


def get_jwks_verifier() -> SupabaseJWKSVerifier:
    """Get the global JWKS verifier instance."""
    if _jwks_verifier is None:
        raise RuntimeError("JWKS verifier not initialized. Call initialize_jwks_verifier() first.")
    return _jwks_verifier