from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db, engine
from app.agents.specialist_agent import MEDICAL_DISCLAIMER

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "medical-reports-api",
    }


@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar_one()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@router.get("/health/cache")
async def health_cache():
    try:
        import redis.asyncio as aioredis
        from app.config import get_settings

        settings = get_settings()
        if not settings.REDIS_URL or settings.REDIS_URL == "redis://localhost:6379/0":
            return {"status": "ok", "cache": "not_configured"}

        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        await r.ping()
        await r.aclose()
        return {"status": "ok", "cache": "connected"}
    except ImportError:
        return {"status": "ok", "cache": "not_installed"}
    except Exception as e:
        return {"status": "error", "cache": str(e)}


@router.get("/health/agents")
async def health_agents():
    return {
        "status": "ok",
        "admin_agent": "CrewAI",
        "specialist_agent": "LangGraph",
        "model_admin": "Claude Haiku 4.5",
        "model_specialist": "Claude Opus 4.6",
        "disclaimer_configured": bool(MEDICAL_DISCLAIMER),
    }
