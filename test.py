from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
import aiosqlite
import string
import random
import segno
import io
import os
import logging
from urllib.parse import urlparse
from untils import get_host_ip
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# ── 設定日誌 ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── 讀取 .env ─────────────────────────────────────────────────────────────────
load_dotenv()

CURRENT_IP = get_host_ip()
DB_PATH = os.getenv("DB_PATH", "shortener.db")
PORT = int(os.getenv("PORT", "8000"))
BASE_URL = os.getenv("BASE_URL", f"http://{CURRENT_IP}:{PORT}")


# ── 合法顏色清單 ─────────────────────────────────────────────────────────────
VALID_COLORS = {
    "black", "white", "red", "green", "blue", "yellow",
    "orange", "purple", "pink", "gray", "grey", "cyan",
    "magenta", "brown", "navy", "teal", "maroon"
}

# ── Lifespan 管理 ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時初始化資料庫
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute('''CREATE TABLE IF NOT EXISTS urls 
                             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                              original_url TEXT, 
                              short_code TEXT UNIQUE,
                              url_count INTEGER DEFAULT 0)''')
        await conn.commit()
    yield

app = FastAPI(lifespan=lifespan)

def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

# ── Short Code 產生 ────────────────────────────────────────────────────────────
async def generate_unique_short_code(conn: aiosqlite.Connection) -> str:
    chars = string.ascii_letters + string.digits
    for _ in range(10):  # 安全極限，避免無窮迴圈
        code = ''.join(random.choice(chars) for _ in range(6))
        async with conn.execute(
            "SELECT 1 FROM urls WHERE short_code = ?", (code,)
        ) as cursor:
            if not await cursor.fetchone():
                return code
    raise Exception("無法生成唯一的短網址代碼")

async def db_url_count(original_url: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        async with conn.execute(
            "SELECT original_url, url_count, short_code FROM urls WHERE original_url = ?", (original_url,)
        ) as cursor:
            return await cursor.fetchone()

# ── 路由 ──────────────────────────────────────────────────────────────────────
@app.get("/")
async def home():
    return {
        "message": f"Server is running on {BASE_URL}",  
        "check_api_in_docs": f"{BASE_URL}/docs"
    }

@app.post("/shorten")
async def shorten_url(original_url: str, color: str = "black"):
    if not is_valid_url(original_url):
        raise HTTPException(status_code=400, detail="Invalid URL. Must start with http:// or https://")

    if color.lower() not in VALID_COLORS:
        raise HTTPException(status_code=400, detail=f"Invalid color '{color}'")

    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            # 查重
            async with conn.execute(
                "SELECT short_code FROM urls WHERE original_url = ?",
                (original_url,)
            ) as cursor:
                url_Existing = await cursor.fetchone()

            if url_Existing:
                short_code = url_Existing[0]
            else:
                retry_count = 3
                while retry_count > 0:
                    short_code = await generate_unique_short_code(conn)
                    try:
                        await conn.execute(
                            "INSERT INTO urls (original_url, short_code) VALUES (?, ?)",
                            (original_url, short_code)
                        )
                        await conn.commit()
                        break
                    except aiosqlite.IntegrityError:
                        retry_count -= 1
                        if retry_count == 0:
                            raise HTTPException(status_code=500, detail="短網址生成失敗，請再試一次。")

        return {
            "short_code": short_code,
            "short_url": f"{BASE_URL}/{short_code}",
            "qr_code_api": f"{BASE_URL}/qr/{short_code}?color={color}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in shorten_url: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")



@app.get("/qr/{short_code}")
async def get_qr(short_code: str, color: str = "black"):
    # 1. 驗證顏色
    if color.lower() not in VALID_COLORS:
         raise HTTPException(status_code=400, detail="Invalid color")

    # 2. 檢查資料庫是否存在該 code (確保這是一個有效的縮網址)
    async with aiosqlite.connect(DB_PATH) as conn:
        async with conn.execute("SELECT 1 FROM urls WHERE short_code = ?", (short_code,)) as cursor:
            result = await cursor.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Short code not found")

    # 3. 【核心修正】QR Code 的內容要是「你的縮網址入口」，而不是原始長網址
    # 這樣使用者掃碼才會回到你的 Server，你才能用 Celery 紀錄數據
    qr_content = f"{BASE_URL}/{short_code}" 
    
    # 4. 生成圖片
    qr = segno.make_qr(qr_content)
    img_buf = io.BytesIO()
    qr.save(img_buf, kind='png', dark=color.lower(), light="white", scale=10)
    img_buf.seek(0)
    
    return StreamingResponse(img_buf, media_type="image/png")

@app.get("/{short_code}")
async def redirect_to_url(short_code: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        async with conn.execute("SELECT original_url FROM urls WHERE short_code = ?", (short_code,)) as cursor:
            result = await cursor.fetchone()

        if result:
            # 更新計數
            await conn.execute("UPDATE urls SET url_count = url_count + 1 WHERE short_code = ?", (short_code,))
            await conn.commit()
            # 2. 自動導向至原始網址
            return RedirectResponse(url=result[0])


    raise HTTPException(status_code=404, detail="Short code not found")

if __name__ == "__main__":
    import uvicorn
    print(f"服務啟動中... 請訪問 {BASE_URL}/docs")
    uvicorn.run("test:app", host="0.0.0.0", port=PORT, reload=True)