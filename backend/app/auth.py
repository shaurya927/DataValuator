from fastapi import Depends, HTTPException, Header
from typing import Optional
from app.config import get_settings, Settings

async def verify_api_key(
    authorization: Optional[str] = Header(None),
    settings: Settings = Depends(get_settings)
):
    """Verify API key if one is configured. No-op when API_KEY is None."""
    if settings.API_KEY is None:
        return  # Auth disabled
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    # Accept both 'Bearer <key>' and raw '<key>'
    token = authorization.replace('Bearer ', '').strip()
    if token != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
