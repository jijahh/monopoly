import asyncio
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Optional
from pydantic import BaseModel

from .connection import room_manager


# Schema for incoming game actions
class GameAction(BaseModel):
    action: str  # e.g., "ROLL_DICE", "BUY_PROPERTY", "END_TURN"
    data: Optional[dict] = None


router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{room_id}")
async def game_websocket_endpoint(websocket: WebSocket, room_id: str):
    player_id = await room_manager.connect(room_id, websocket)

    # Broadcast to room that a new opponent entered
    await room_manager.broadcast_to_room(
        room_id,
        {
            "type": "PLAYER_JOINED",
            "player_id": player_id,
            "message": f"Player {player_id} entered the game.",
        },
    )

    try:
        while True:
            # Receive structured data from client
            raw_data = await websocket.receive_json()

            # (Optional) Validate using Pydantic if desired
            action_packet = GameAction(**raw_data)

            # Handle turn-based Monopoly mechanics
            if action_packet.action == "ROLL_DICE":
                # In production, process your Monopoly state engine here
                import random

                die1, die2 = random.randint(1, 6), random.randint(1, 6)

                await room_manager.broadcast_to_room(
                    room_id,
                    {
                        "type": "DICE_ROLLED",
                        "player_id": player_id,
                        "rolls": [die1, die2],
                        "total": die1 + die2,
                    },
                )

            elif action_packet.action == "END_TURN":
                await room_manager.broadcast_to_room(
                    room_id,
                    {
                        "type": "TURN_CHANGED",
                        "previous_player": player_id,
                        "message": "Next player's turn!",
                    },
                )

    except WebSocketDisconnect:
        room_manager.disconnect(room_id, player_id)
        await room_manager.broadcast_to_room(
            room_id,
            {
                "type": "PLAYER_LEFT",
                "player_id": player_id,
                "message": f"Player {player_id} disconnected.",
            },
        )
