from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import segno
import io

from infra.db import get_db
from infra.models import URLRecord
from config import settings

router = APIRouter()

VALID_COLORS = {
    "black", "white", "red", "green", "blue", "yellow",
    "orange", "purple", "pink", "gray", "grey", "cyan",
    "magenta", "brown", "navy", "teal", "maroon"
}

@router.get("/qr/{short_code}")
async def get_qr(short_code: str, color: str = "black", db: AsyncSession = Depends(get_db)):
    if color.lower() not in VALID_COLORS:
        raise HTTPException(status_code=400, detail="Invalid color")

    stmt = select(URLRecord).where(URLRecord.short_code == short_code)
    result = await db.execute(stmt)
    url_record = result.scalars().first()

    if not url_record:
        raise HTTPException(status_code=404, detail="Short code not found")

    qr_content = f"{settings.resolved_base_url}/{short_code}"
    
    qr = segno.make_qr(qr_content)
    img_buf = io.BytesIO()
    qr.save(img_buf, kind='png', dark=color.lower(), light="white", scale=10)
    img_buf.seek(0)
    return StreamingResponse(img_buf, media_type="image/png")
