import asyncio
import json
import uuid
from dataclasses import dataclass
from typing import Optional

from fastapi import WebSocket
from redis.asyncio import Redis
from redis.exceptions import WatchError

ROOM_TTL = 24 * 60 * 60  # 24 hours
PLAYER_LEASE_TTL = 90  # A connection expires after 90 seconds
HEARTBEAT_INTERVAL = 25  # Refresh the lease every 25 seconds
MAX_PLAYERS = 8


@dataclass
class LocalConnection:
    player_id: str
    name: str
    role: str
    token: str
    websocket: WebSocket
    heartbeat_task: Optional[asyncio.Task] = None


class RoomManager:
    def __init__(self):
        self.redis: Optional[Redis] = None

        # Actual WebSocket objects must stay in local memory.
        # Each Vercel instance has its own version of this mapping.
        self.local_connections: dict[str, dict[str, LocalConnection]] = {}

        # One Redis Pub/Sub listener per room, per server instance.
        self.pubsub_tasks: dict[str, asyncio.Task] = {}
        self.pubsub_ready: dict[str, asyncio.Event] = {}

    async def initialize(self, redis_client: Redis):
        self.redis = redis_client

    async def shutdown(self):
        tasks = list(self.pubsub_tasks.values())

        for connections in self.local_connections.values():
            for client in connections.values():
                if client.heartbeat_task:
                    client.heartbeat_task.cancel()

        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

        self.local_connections.clear()
        self.pubsub_tasks.clear()
        self.pubsub_ready.clear()

    def _require_redis(self):
        if self.redis is None:
            raise RuntimeError("Redis has not been initialized.")

        return self.redis

    def _room_key(self, room_id: str) -> str:
        return f"room:{room_id}"

    def _channel(self, room_id: str) -> str:
        return f"room:{room_id}:events"

    def _lease_key(self, room_id: str, player_id: str) -> str:
        return f"room:{room_id}:player:{player_id}:connection"

    # ---------------------------------------------------------
    # ROOM CREATION AND LOOKUP
    # ---------------------------------------------------------

    async def create_room(self, room_id: str) -> bool:
        redis = self._require_redis()

        room = {
            "room_id": room_id,
            "status": "waiting",
            "players": {},
            "host_player_id": None,
            "game": None,
        }

        return bool(
            await redis.set(
                self._room_key(room_id),
                json.dumps(room),
                ex=ROOM_TTL,
                nx=True,
            )
        )

    async def get_room(self, room_id: str):
        redis = self._require_redis()

        raw_room = await redis.get(self._room_key(room_id))

        if raw_room is None:
            return None

        return json.loads(raw_room)

    # ---------------------------------------------------------
    # PUB/SUB
    # ---------------------------------------------------------

    async def _ensure_listener(self, room_id: str):
        task = self.pubsub_tasks.get(room_id)

        if task is None or task.done():
            ready = asyncio.Event()

            task = asyncio.create_task(self._listen_room(room_id, ready))

            self.pubsub_tasks[room_id] = task
            self.pubsub_ready[room_id] = ready

        ready = self.pubsub_ready[room_id]

        try:
            await asyncio.wait_for(ready.wait(), timeout=10)
        except asyncio.TimeoutError:
            raise RuntimeError(f"Could not subscribe to room {room_id}.")

        if task.done():
            raise RuntimeError(f"Redis listener for room {room_id} stopped.")

    async def _listen_room(
        self,
        room_id: str,
        ready: asyncio.Event,
    ):
        redis = self._require_redis()

        try:
            while True:
                try:
                    async with redis.pubsub() as pubsub:
                        await pubsub.subscribe(self._channel(room_id))
                        ready.set()

                        async for message in pubsub.listen():
                            if message["type"] != "message":
                                continue

                            try:
                                payload = json.loads(message["data"])
                            except TypeError, json.JSONDecodeError:
                                print(f"[PUBSUB] Invalid message in {room_id}")
                                continue

                            await self._deliver_to_local_players(
                                room_id,
                                payload,
                            )

                            # No local clients remain on this instance.
                            if not self.local_connections.get(room_id):
                                return
                        if payload.get("type") == "_CONNECTION_REPLACED":
                            await self._handle_replaced_connection(
                                room_id,
                                payload["player_id"],
                                payload["token"],
                            )
                            continue

                except asyncio.CancelledError:
                    raise

                except Exception as exc:
                    print(f"[PUBSUB] Listener error in {room_id}: {exc}")

                    if not self.local_connections.get(room_id):
                        return

                    # Try to resubscribe if the Redis connection drops.
                    await asyncio.sleep(1)

        finally:
            ready.set()

            current_task = asyncio.current_task()

            if self.pubsub_tasks.get(room_id) is current_task:
                self.pubsub_tasks.pop(room_id, None)
                self.pubsub_ready.pop(room_id, None)

    async def _deliver_to_local_players(
        self,
        room_id: str,
        payload: dict,
    ):
        connections = list(self.local_connections.get(room_id, {}).items())

        results = await asyncio.gather(
            *(client.websocket.send_json(payload) for player_id, client in connections),
            return_exceptions=True,
        )

        for (player_id, client), result in zip(connections, results):
            if isinstance(result, BaseException):
                print(f"[BROADCAST] Failed to send to {client.name}: " f"{result}")

                disconnected = await self.disconnect(
                    room_id,
                    player_id,
                    client.token,
                    client.websocket,
                )

                if disconnected:
                    await self.broadcast_to_room(
                        room_id,
                        {
                            "type": "PLAYER_LEFT",
                            "player_id": player_id,
                            "player_name": client.name,
                        },
                    )

    async def broadcast_to_room(self, room_id: str, payload: dict):
        """Publish an event so every instance subscribed to this room receives it."""
        redis = self._require_redis()

        await redis.publish(
            self._channel(room_id),
            json.dumps(payload),
        )

    # ---------------------------------------------------------
    # PLAYER CONNECTION AND RECONNECTION
    # ---------------------------------------------------------

    async def connect(
        self,
        room_id: str,
        name: str,
        websocket: WebSocket,
    ):
        redis = self._require_redis()

        name = name.strip()

        if not name:
            raise ValueError("A player name is required.")

        # Start listening before this instance joins the room.
        await self._ensure_listener(room_id)

        # Accept the WebSocket before registering the connection.
        await websocket.accept()

        room_key = self._room_key(room_id)

        try:
            for attempt in range(5):
                async with redis.pipeline(transaction=True) as pipe:
                    try:
                        await pipe.watch(room_key)

                        raw_room = await pipe.get(room_key)

                        if raw_room is None:
                            raise ValueError("Room does not exist.")

                        room = json.loads(raw_room)
                        players = room["players"]

                        # Find an existing player with this name.
                        existing = next(
                            (
                                (pid, player)
                                for pid, player in players.items()
                                if player["name"].casefold() == name.casefold()
                            ),
                            None,
                        )

                        if room["status"] != "waiting" and room["status"] != "playing":
                            raise ValueError("This game is no longer available.")

                        if room["status"] == "playing" and existing is None:
                            raise ValueError(
                                "The game has already started; "
                                "new players cannot join."
                            )

                        if existing:
                            player_id, player = existing
                        else:
                            if len(players) >= MAX_PLAYERS:
                                raise ValueError("This room is full.")

                            player_id = uuid.uuid4().hex[:12]

                            if room["host_player_id"] is None:
                                role = "host"
                                room["host_player_id"] = player_id
                            else:
                                role = "client"

                            player = {
                                "player_id": player_id,
                                "name": name,
                                "role": role,
                                "connection_token": None,
                            }

                            players[player_id] = player

                        lease_key = self._lease_key(
                            room_id,
                            player_id,
                        )

                        # Watch the connection lease too. This prevents two
                        # clients from claiming the same player simultaneously.

                        active_token = await pipe.get(lease_key)

                        if active_token is not None:
                            raise ValueError("That player name is already connected.")

                        token = uuid.uuid4().hex
                        player["connection_token"] = token

                        pipe.multi()

                        pipe.set(
                            room_key,
                            json.dumps(room),
                            ex=ROOM_TTL,
                        )

                        pipe.set(
                            lease_key,
                            token,
                            ex=PLAYER_LEASE_TTL,
                        )

                        await pipe.execute()

                        # If an old local socket for this player still exists,
                        # close it before replacing the local reference.
                        old_client = self.local_connections.get(room_id, {}).get(
                            player_id
                        )

                        if old_client is not None:
                            try:
                                await old_client.websocket.close(
                                    code=4001,
                                    reason="Player reconnected elsewhere.",
                                )
                            except Exception:
                                pass

                            self._remove_local_connection(
                                room_id,
                                player_id,
                            )

                        client = LocalConnection(
                            player_id=player_id,
                            name=player["name"],
                            role=player["role"],
                            token=token,
                            websocket=websocket,
                        )

                        self.local_connections.setdefault(room_id, {})[
                            player_id
                        ] = client

                        client.heartbeat_task = asyncio.create_task(
                            self._heartbeat(
                                room_id,
                                player_id,
                                token,
                            )
                        )
                        try:
                            await self.broadcast_to_room(
                                room_id,
                                {
                                    "type": "_CONNECTION_REPLACED",
                                    "player_id": player_id,
                                    "token": token,
                                },
                            )
                        except Exception as exc:
                            print(f"[CONNECT] Could not notify old connection: {exc}")

                        return (
                            player_id,
                            player["role"],
                            player["name"],
                            token,
                            room["status"],
                        )

                    except WatchError:
                        if attempt == 4:
                            raise RuntimeError(
                                "Could not register player. "
                                "Please try connecting again."
                            )

                        continue

        except Exception:
            await self._stop_listener_if_idle(room_id)
            raise

    async def _heartbeat(
        self,
        room_id: str,
        player_id: str,
        token: str,
    ):
        redis = self._require_redis()
        lease_key = self._lease_key(room_id, player_id)
        room_key = self._room_key(room_id)

        script = """
        if redis.call('GET', KEYS[1]) == ARGV[1] then
            redis.call('EXPIRE', KEYS[1], ARGV[2])
            redis.call('EXPIRE', KEYS[2], ARGV[3])
            return 1
        end
        return 0
        """

        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)

            try:
                refreshed = await redis.eval(
                    script,
                    2,
                    lease_key,
                    room_key,
                    token,
                    PLAYER_LEASE_TTL,
                    ROOM_TTL,
                )

                if not refreshed:
                    return

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                # A temporary Redis error should not permanently stop
                # this connection's heartbeat.
                print(f"[HEARTBEAT] Error for player {player_id}: {exc}")

    # ---------------------------------------------------------
    # DISCONNECTION
    # ---------------------------------------------------------

    def _remove_local_connection(
        self,
        room_id: str,
        player_id: str,
    ):
        connections = self.local_connections.get(room_id)

        if not connections:
            return

        client = connections.pop(player_id, None)

        if client and client.heartbeat_task:
            if client.heartbeat_task is not asyncio.current_task():
                client.heartbeat_task.cancel()

        if not connections:
            self.local_connections.pop(room_id, None)

    async def _stop_listener_if_idle(self, room_id: str):
        if self.local_connections.get(room_id):
            return

        task = self.pubsub_tasks.get(room_id)

        if task and task is not asyncio.current_task():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def disconnect(
        self,
        room_id: str,
        player_id: str,
        token: str,
        websocket: WebSocket,
    ) -> bool:
        redis = self._require_redis()

        local_client = self.local_connections.get(room_id, {}).get(player_id)

        # Never let an older socket disconnect a newer connection.
        if (
            local_client is None
            or local_client.websocket is not websocket
            or local_client.token != token
        ):
            return False

        room_key = self._room_key(room_id)
        lease_key = self._lease_key(room_id, player_id)

        try:
            for attempt in range(5):
                async with redis.pipeline(transaction=True) as pipe:
                    try:
                        await pipe.watch(room_key)

                        raw_room = await pipe.get(room_key)
                        active_token = await pipe.get(lease_key)

                        if raw_room is None:
                            self._remove_local_connection(
                                room_id,
                                player_id,
                            )
                            return False

                        room = json.loads(raw_room)
                        player = room["players"].get(player_id)

                        if (
                            player is None
                            or player.get("connection_token") != token
                            or active_token != token
                        ):
                            # Another connection has already replaced this one.
                            self._remove_local_connection(
                                room_id,
                                player_id,
                            )
                            return False

                        if room["status"] == "playing":
                            # Retain the player so they can reconnect.
                            player["connection_token"] = None
                        else:
                            # Waiting-room players are removed on disconnect.
                            room["players"].pop(player_id, None)

                            if room["host_player_id"] == player_id:
                                room["host_player_id"] = None

                                # Promote the next remaining player.
                                for other_id, other in room["players"].items():
                                    other["role"] = "host"
                                    room["host_player_id"] = other_id
                                    break

                        pipe.multi()

                        pipe.set(
                            room_key,
                            json.dumps(room),
                            ex=ROOM_TTL,
                        )

                        pipe.delete(lease_key)

                        await pipe.execute()

                        self._remove_local_connection(
                            room_id,
                            player_id,
                        )

                        await self._stop_listener_if_idle(room_id)
                        return True

                    except WatchError:
                        if attempt == 4:
                            raise RuntimeError(
                                "Could not complete player disconnection."
                            )

                        continue

        except Exception:
            raise

        return False

    # ---------------------------------------------------------
    # GAME ACTIONS
    # ---------------------------------------------------------

    async def handle_action(
        self,
        room_id: str,
        player_id: str,
        token: str,
        action: str,
        data: Optional[dict] = None,
    ):
        redis = self._require_redis()
        room_key = self._room_key(room_id)

        from monopoly.main_game import Game

        for attempt in range(5):
            async with redis.pipeline(transaction=True) as pipe:
                try:
                    await pipe.watch(room_key)

                    raw_room = await pipe.get(room_key)

                    if raw_room is None:
                        raise ValueError("This room is no longer available.")

                    room = json.loads(raw_room)
                    player = room["players"].get(player_id)

                    if player is None:
                        raise ValueError("You are no longer in this room.")

                    lease_key = self._lease_key(room_id, player_id)

                    active_token = await pipe.get(lease_key)

                    if player.get("connection_token") != token or active_token != token:
                        raise ValueError(
                            "This connection is no longer active. " "Please reconnect."
                        )

                    action = action.strip().upper()

                    if action == "START_GAME":
                        if player["role"] != "host":
                            raise ValueError("Only the host can start the game.")

                        if room["status"] != "waiting":
                            raise ValueError("The game has already started.")

                        names = [p["name"] for p in room["players"].values()]

                        if len(names) < 2:
                            raise ValueError(
                                "At least two players must join " "before starting."
                            )

                        game = Game(names)

                        room["game"] = game.to_dict()
                        room["status"] = "playing"

                        events = [
                            {
                                "type": "GAME_STARTED",
                                "state": room["game"],
                            }
                        ]

                    else:
                        if room["status"] != "playing" or room["game"] is None:
                            raise ValueError("The host must start the game first.")

                        game = Game.from_dict(room["game"])

                        events = game.handle_action(
                            player["name"],
                            action,
                            data,
                        )

                        room["game"] = game.to_dict()

                        if game.winner is not None:
                            room["status"] = "finished"

                    pipe.multi()

                    pipe.set(
                        room_key,
                        json.dumps(room),
                        ex=ROOM_TTL,
                    )

                    await pipe.execute()

                    return events

                except WatchError:
                    if attempt == 4:
                        raise RuntimeError(
                            "The game state changed too frequently. "
                            "Please try your action again."
                        )

                    continue

        return []

    async def _handle_replaced_connection(
        self,
        room_id: str,
        player_id: str,
        new_token: str,
    ):
        old_client = self.local_connections.get(room_id, {}).get(player_id)

        if old_client is None or old_client.token == new_token:
            return

        try:
            await old_client.websocket.close(
                code=4001,
                reason="Player reconnected.",
            )
        except Exception:
            pass

        await self.disconnect(
            room_id,
            player_id,
            old_client.token,
            old_client.websocket,
        )


room_manager = RoomManager()
