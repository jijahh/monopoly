import os
from contextlib import asynccontextmanager

import redis.asyncio as redis
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from monopoly.api_routes import router as rooms_router
from monopoly.connection import room_manager
from monopoly.websocket import router as websocket_router

# Load .env during local development.
# Vercel supplies its environment variables separately.
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        raise RuntimeError("REDIS_URL environment variable is missing.")

    redis_client = redis.from_url(
        redis_url,
        decode_responses=True,
        health_check_interval=30,
    )

    # Fail application startup if Redis is unreachable.
    await redis_client.ping()

    await room_manager.initialize(redis_client)

    try:
        yield

    finally:
        await room_manager.shutdown()
        await redis_client.aclose()


app = FastAPI(
    title="Monopoly WebSocket API",
    description="Room management and real-time Monopoly game actions.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rooms_router)
app.include_router(websocket_router)


@app.get("/")
async def root():
    return {"message": "Monopoly WebSocket API is running."}


@app.get("/health")
async def health():
    try:
        await room_manager.redis.ping()
        return {"status": "ok", "redis": "connected"}

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Redis connection failed.",
        )
