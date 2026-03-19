from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import string
import random
import logging

from config import settings
from infra.db import get_db
from infra.models import URLRecord

logger = logging.getLogger(__name__)
router = APIRouter()

VALID_COLORS = {
    "black", "white", "red", "green", "blue", "yellow",
    "orange", "purple", "pink", "gray", "grey", "cyan",
    "magenta", "brown", "navy", "teal", "maroon"
}

def is_valid_url(url: str) -> bool:
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

async def generate_unique_short_code(db: AsyncSession) -> str:
    chars = string.ascii_letters + string.digits
    for _ in range(10):
        code = ''.join(random.choice(chars) for _ in range(6))
        stmt = select(URLRecord).where(URLRecord.short_code == code)
        result = await db.execute(stmt)
        if not result.scalars().first():
            return code
    raise Exception("無法生成唯一的短網址代碼")

@router.post("/shorten")
async def shorten_url(original_url: str, color: str = "black", db: AsyncSession = Depends(get_db)):
    if not is_valid_url(original_url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    if color.lower() not in VALID_COLORS:
        raise HTTPException(status_code=400, detail="Invalid color")

    try:
        stmt = select(URLRecord).where(URLRecord.original_url == original_url)
        result = await db.execute(stmt)
        url_existing = result.scalars().first()

        if url_existing:
            short_code = url_existing.short_code
        else:
            retry_count = 3
            while retry_count > 0:
                short_code = await generate_unique_short_code(db)
                try:
                    new_url = URLRecord(original_url=original_url, short_code=short_code)
                    db.add(new_url)
                    await db.commit()
                    break
                except IntegrityError:
                    await db.rollback()
                    retry_count -= 1
                    if retry_count == 0:
                        raise HTTPException(status_code=500, detail="短網址生成失敗")

        return {
            "short_code": short_code,
            "short_url": f"{settings.resolved_base_url}/{short_code}",
            "qr_code_api": f"{settings.resolved_base_url}/qr/{short_code}?color={color}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
