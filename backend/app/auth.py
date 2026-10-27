"""
auth.py

Verifies Clerk session tokens on the backend using standard JWT + JWKS
verification.

HOW IT WORKS
  1. The frontend Clerk React SDK sends the signed-in user's session token
     as:
         Authorization: Bearer <token>

  2. This module fetches Clerk's public signing keys (JWKS), caches them,
     and verifies:
       - JWT signature
       - issuer
       - expiration
       - issued-at timestamp

  3. A small clock-skew allowance is used because the browser/Clerk server
     and the local development machine may differ by a few seconds.

  4. On successful verification, the Clerk user ID and email are returned.

GRACEFUL DEGRADATION:
If Clerk authentication is not configured, optional-auth endpoints continue
to work in guest mode.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Optional

import jwt
from jwt import PyJWKClient
from fastapi import Header, HTTPException

from app.config import settings


logger = logging.getLogger("cxiq")


# =========================================================
# JWKS CACHE
# =========================================================

_jwk_client: Optional[PyJWKClient] = None
_jwk_client_created_at: float = 0

_JWK_CLIENT_TTL_SECONDS = 3600


# Small allowance for clock differences between:
# - local Windows machine
# - browser
# - Clerk servers
#
# This does NOT disable token validation.
JWT_CLOCK_SKEW_SECONDS = 60


# =========================================================
# JWKS CLIENT
# =========================================================

def _get_jwk_client() -> Optional[PyJWKClient]:

    global _jwk_client, _jwk_client_created_at

    if not settings.AUTH_ENABLED:
        return None

    now = time.time()

    if (
        _jwk_client is None
        or (now - _jwk_client_created_at) > _JWK_CLIENT_TTL_SECONDS
    ):
        _jwk_client = PyJWKClient(
            settings.CLERK_JWKS_URL
        )

        _jwk_client_created_at = now

    return _jwk_client


# =========================================================
# TOKEN VERIFICATION
# =========================================================

def _verify_token(token: str) -> Optional[Dict]:

    client = _get_jwk_client()

    if client is None:
        return None

    try:

        # Get Clerk's public signing key corresponding to
        # the key ID contained in this JWT.
        signing_key = client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,

            algorithms=["RS256"],

            issuer=settings.CLERK_ISSUER,

            # Clerk session tokens may not always contain a
            # conventional audience value.
            options={
                "verify_aud": False,
            },

            # IMPORTANT:
            # Allows a small clock difference without disabling
            # iat/exp verification.
            leeway=JWT_CLOCK_SKEW_SECONDS,
        )

        return payload

    except jwt.ExpiredSignatureError:

        logger.info(
            "Clerk token verification failed: token has expired."
        )

        return None

    except jwt.ImmatureSignatureError:

        logger.info(
            "Clerk token verification failed: token is not yet valid "
            "(possible clock difference)."
        )

        return None

    except jwt.InvalidIssuerError:

        logger.info(
            "Clerk token verification failed: invalid issuer."
        )

        return None

    except jwt.PyJWTError as exc:

        logger.info(
            "Clerk token verification failed: %s",
            exc,
        )

        return None

    except Exception as exc:

        logger.warning(
            "Unexpected error verifying Clerk token: %s",
            exc,
        )

        return None


# =========================================================
# OPTIONAL AUTHENTICATION
# =========================================================

def get_current_user_optional(
    authorization: Optional[str] = Header(default=None),
) -> Optional[Dict]:

    """
    Returns:

        {
            "clerk_user_id": "...",
            "email": "..."
        }

    when a valid Clerk session token is available.

    Otherwise returns None.

    This dependency is used by endpoints that support both
    signed-in users and guest users.
    """

    if not settings.AUTH_ENABLED:
        return None

    if not authorization:
        return None

    if not authorization.lower().startswith("bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()

    if not token:
        return None

    payload = _verify_token(token)

    if not payload:
        return None


    # -----------------------------------------------------
    # Clerk User ID
    # -----------------------------------------------------

    clerk_user_id = payload.get("sub")

    if not clerk_user_id:
        logger.info(
            "Clerk token verified but contains no 'sub' claim."
        )

        return None


    # -----------------------------------------------------
    # Email
    # -----------------------------------------------------

    email = payload.get("email")

    if not email:

        email_addresses = payload.get("email_addresses")

        if isinstance(email_addresses, list) and email_addresses:

            first_email = email_addresses[0]

            if isinstance(first_email, dict):
                email = first_email.get("email_address")


    return {
        "clerk_user_id": clerk_user_id,
        "email": email,
    }


# =========================================================
# REQUIRED AUTHENTICATION
# =========================================================

def require_user(
    authorization: Optional[str] = Header(default=None),
) -> Dict:

    """
    Dependency for endpoints that require authentication.

    Unlike get_current_user_optional(), this raises HTTP 401
    when no valid Clerk session is available.
    """

    user = get_current_user_optional(authorization)

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Sign in required for this feature.",
        )

    return user