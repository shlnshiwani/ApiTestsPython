"""
dependencies/headers.py
~~~~~~~~~~~~~~~~~~~~~~~~
FastAPI dependency for header validation.

All employee endpoints require:
  - X-API-Key: secret123      (authentication)
  - Accept: application/json  (content negotiation)

Inject `require_headers` via Depends() at the router or individual route level.
"""

from fastapi import Header, HTTPException, status

# Hardcoded for demo — in production, load from env / secrets manager
VALID_API_KEY = "secret123"


async def require_headers(
    x_api_key: str = Header(
        ...,
        description="API key for authentication. Use value: **secret123**",
        example="secret123",
    ),
    accept: str = Header(
        default="application/json",
        description="Must include application/json",
        example="application/json",
    ),
) -> None:
    """
    Shared dependency applied to every employee endpoint.

    Validates:
    1. X-API-Key header is present and equals the expected key.
    2. Accept header includes 'application/json'.

    Raises HTTP 401 for a missing or wrong API key.
    Raises HTTP 406 when the client does not accept JSON responses.
    """
    if x_api_key != VALID_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header. Expected: secret123",
        )

    if "application/json" not in accept and "*/*" not in accept:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Accept header must include 'application/json'",
        )
