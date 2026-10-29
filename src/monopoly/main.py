from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from monopoly.api_routes import router as rooms_router
from monopoly.websocket import router as websocket_router

app = FastAPI(
    title="Monopoly WebSocket API",
    description="Room management and real-time Monopoly game actions.",
    version="1.0.0",
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
    return {"status": "ok"}
