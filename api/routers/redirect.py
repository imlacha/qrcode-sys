from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from infra.db import get_db
from infra.models import URLRecord
from infra.cache import cache

router = APIRouter()

@router.get("/{short_code}")
async def redirect_to_url(short_code: str, db: AsyncSession = Depends(get_db)):
    original_url = await cache.get(short_code)
    
    if original_url:
        await cache.increment(f"clicks:{short_code}")
        return generate_html_redirect(original_url)

    stmt = select(URLRecord).where(URLRecord.short_code == short_code)
    result = await db.execute(stmt)
    url_record = result.scalars().first()

    if url_record:
        original_url = url_record.original_url
        await cache.set(short_code, original_url, ex=86400)
        await cache.increment(f"clicks:{short_code}")
        
        update_stmt = update(URLRecord).where(URLRecord.short_code == short_code).values(url_count=URLRecord.url_count + 1)
        await db.execute(update_stmt)
        await db.commit()
        return generate_html_redirect(original_url)

    raise HTTPException(status_code=404, detail="Short code not found")

def generate_html_redirect(original_url: str) -> HTMLResponse:
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>Redirecting...</title></head>
    <body>
        <p>正在為您轉跳至目標網址...</p>
        <script>window.location.replace("{original_url}");</script>
        <noscript><a href="{original_url}">點擊這裡前往</a></noscript>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
