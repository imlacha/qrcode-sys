from fastapi import FastAPI
from contextlib import asynccontextmanager
from config import settings
from infra.db import init_db
from infra.cache import cache
from api.routers import shorten, redirect, qr
import logging

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await cache.connect()
    yield
    await cache.disconnect()

app = FastAPI(lifespan=lifespan)

app.include_router(shorten.router, tags=["shorten"])
app.include_router(qr.router, tags=["qr"])
app.include_router(redirect.router, tags=["redirect"])

@app.get("/")
async def home():
    return {
        "message": f"Server is running on {settings.resolved_base_url}",  
        "check_api_in_docs": f"{settings.resolved_base_url}/docs"
    }
