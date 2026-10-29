from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import your route files
from . import api_routes
from . import websocket

app = FastAPI(title="Monopoly Game Server")

# Configure CORS for your decoupled frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect the routers to your main application instance
app.include_router(api_routes.router)
app.include_router(websocket.router)
