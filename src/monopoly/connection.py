import asyncio
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict


class RoomManager:
    def __init__(self):
        # Structure: { room_id: { player_id: websocket } }
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket) -> str:
        """Accepts connection, initializes room if new, and assigns player ID."""
        await websocket.accept()

        # Create room dictionary if it doesn't exist yet
        if room_id not in self.rooms:
            self.rooms[room_id] = {}

        player_id = f"player_{str(uuid.uuid4())[:6]}"
        self.rooms[room_id][player_id] = websocket

        # Welcome payload scoped to the room setup
        await websocket.send_json(
            {"type": "WELCOME", "room_id": room_id, "player_id": player_id}
        )
        return player_id

    def disconnect(self, room_id: str, player_id: str):
        """Safely removes a player and cleans up empty rooms."""
        if room_id in self.rooms:
            self.rooms[room_id].pop(player_id, None)
            # Delete the room entirely if no players are left
            if not self.rooms[room_id]:
                self.rooms.pop(room_id, None)

    async def broadcast_to_room(self, room_id: str, payload: dict):
        """Sends a JSON payload concurrently only to players inside a specific room."""
        if room_id not in self.rooms:
            return

        room_clients = self.rooms[room_id]
        player_ids = list(room_clients.keys())
        connections = list(room_clients.values())

        # Fire notifications concurrently
        results = await asyncio.gather(
            *[conn.send_json(payload) for conn in connections], return_exceptions=True
        )

        # Handle mid-broadcast disconnections
        for player_id, result in zip(player_ids, results):
            if isinstance(result, (WebSocketDisconnect, Exception)):
                self.disconnect(room_id, player_id)


room_manager = RoomManager()
