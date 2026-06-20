import pyotp
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.security import get_current_user

router = APIRouter(prefix="/auth/2fa", tags=["2fa"])


@router.post("/setup")
async def setup_2fa(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.two_fa_enabled:
        raise HTTPException(status_code=400, detail="2FA already enabled")

    secret = pyotp.random_base32()
    user.two_fa_secret = secret
    await db.flush()

    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name="MedicalReports",
    )

    return {
        "secret": secret,
        "qr_code_uri": provisioning_uri,
    }


@router.post("/verify")
async def verify_2fa(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.two_fa_secret:
        raise HTTPException(
            status_code=400, detail="2FA not set up. Call /auth/2fa/setup first"
        )

    totp = pyotp.TOTP(user.two_fa_secret)
    if not totp.verify(code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")

    user.two_fa_enabled = True
    await db.flush()

    return {"status": "2fa_enabled"}


@router.post("/disable")
async def disable_2fa(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.two_fa_enabled or not user.two_fa_secret:
        raise HTTPException(status_code=400, detail="2FA not enabled")

    totp = pyotp.TOTP(user.two_fa_secret)
    if not totp.verify(code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")

    user.two_fa_enabled = False
    user.two_fa_secret = None
    await db.flush()

    return {"status": "2fa_disabled"}


@router.get("/status")
async def get_2fa_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"two_fa_enabled": user.two_fa_enabled}
