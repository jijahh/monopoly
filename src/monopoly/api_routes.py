import uuid
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# Import the shared state instance
from .connection import room_manager

# Create the router object
router = APIRouter(prefix="/api/rooms", tags=["Rooms"])


class JoinRoomRequest(BaseModel):
    room_code: str


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_room():
    room_id = str(uuid.uuid4())[:8]

    # Access the shared room manager to register the room
    room_manager.rooms[room_id] = {
        "status": "waiting",
        "board_state": {},
    }

    return {
        "success": True,
        "room_id": room_id,
        "message": "Room initialized successfully.",
    }


@router.post("/join")
async def join_room(payload: JoinRoomRequest):
    room_id = payload.room_code.strip().lower()

    # Access the shared room manager to validate the code
    if room_id not in room_manager.rooms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested game room code does not exist.",
        )

    return {"success": True, "room_id": room_id, "message": "Access granted to room."}
