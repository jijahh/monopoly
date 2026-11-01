from typing import Optional
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

from .connection import room_manager


class GameAction(BaseModel):
    action: str
    data: Optional[dict] = None


router = APIRouter(tags=["WebSocket"])


async def send_error(websocket: WebSocket, message: str):
    await websocket.send_json(
        {
            "type": "ERROR",
            "message": message,
        }
    )


@router.websocket("/ws/{room_id}")
async def game_websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    name: str = Query(...),
):
    player_id = None
    player_name = None
    token = None

    try:
        (
            player_id,
            role,
            player_name,
            token,
            room_status,
        ) = await room_manager.connect(
            room_id,
            name,
            websocket,
        )

    except ValueError as exc:
        await websocket.close(code=1008, reason=str(exc))
        return

    except Exception as exc:
        print(f"[CONNECT] Unexpected error: {exc}")
        await websocket.close(
            code=1011,
            reason="Could not connect to the game server.",
        )
        return

    try:
        await websocket.send_json(
            {
                "type": "WELCOME",
                "room_id": room_id,
                "player_id": player_id,
                "player_name": player_name,
                "role": role,
                "status": room_status,
            }
        )

        await room_manager.broadcast_to_room(
            room_id,
            {
                "type": "PLAYER_JOINED",
                "player_id": player_id,
                "player_name": player_name,
                "role": role,
            },
        )

        while True:
            try:
                raw_data = await websocket.receive_json()

            except json.JSONDecodeError:
                await send_error(
                    websocket,
                    "Malformed JSON. Please send a valid JSON object.",
                )
                continue

            except WebSocketDisconnect:
                break

            try:
                packet = GameAction(**raw_data)

            except (ValidationError, TypeError) as exc:
                await send_error(
                    websocket,
                    f"Invalid action message: {exc}",
                )
                continue

            try:
                events = await room_manager.handle_action(
                    room_id=room_id,
                    player_id=player_id,
                    token=token,
                    action=packet.action,
                    data=packet.data,
                )

                for event in events:
                    await room_manager.broadcast_to_room(
                        room_id,
                        event,
                    )

            except ValueError as exc:
                await send_error(websocket, str(exc))
                continue

            except Exception as exc:
                print(f"[GAME ACTION] Unexpected error: {exc}")

                await send_error(
                    websocket,
                    "An internal server error occurred while "
                    "processing your action.",
                )
                continue

    except WebSocketDisconnect:
        pass

    except Exception as exc:
        print(f"[WEBSOCKET] Error for {player_name}: {exc}")

    finally:
        try:
            disconnected = await room_manager.disconnect(
                room_id,
                player_id,
                token,
                websocket,
            )

            # Only broadcast PLAYER_LEFT if this exact connection
            # successfully changed the room's connection state.
            if disconnected:
                await room_manager.broadcast_to_room(
                    room_id,
                    {
                        "type": "PLAYER_LEFT",
                        "player_id": player_id,
                        "player_name": player_name,
                    },
                )

        except Exception as exc:
            print(f"[DISCONNECT] Cleanup failed for {player_name}: {exc}")
