# Monopoly Game Backend

A real-time multiplayer Monopoly game backend built with **Python, FastAPI, WebSockets, and Redis**. It provides room management, player connections, and synchronized game state across multiple server instances.

The backend is deployed on **Vercel**, with **Upstash Redis** handling shared room state, connection management, and cross-instance communication.

## Live Deployment

**Base URL:** https://monopoly-chi-lime.vercel.app/

**Interactive API Documentation:** https://monopoly-chi-lime.vercel.app/docs

**Health Check:** https://monopoly-chi-lime.vercel.app/health

The deployed API can be used directly by clients to create and join game rooms.

## Tech Stack

- **Python** – Backend programming language
- **FastAPI** – HTTP API and WebSocket framework
- **Uvicorn** – ASGI server for local development
- **WebSockets** – Real-time communication between players and the server
- **Redis (Upstash)** – Shared game-room state, connection leases, and Pub/Sub messaging
- **Vercel** – Backend deployment and hosting

## Architecture

The backend uses Redis to coordinate game rooms and player connections across multiple server instances.

This is particularly important in a serverless environment, where different players connecting to the same room may be handled by different instances.

### Redis Responsibilities

- **Shared Room State:** Stores room information, player data, and serialized game state.
- **Pub/Sub Messaging:** Broadcasts events between server instances so players can receive updates regardless of which instance they are connected to.
- **Connection Leases:** Tracks active player connections using temporary Redis keys with expiration times.
- **Connection Recovery:** Uses connection tokens and heartbeats to manage reconnections and detect stale connections.
- **Atomic Updates:** Uses Redis transactions and optimistic locking (`WATCH`, `MULTI`, and `EXEC`) to help prevent conflicting game-state updates.

### WebSocket Connections

Actual WebSocket connections remain local to the server instance handling them. Redis does not store WebSocket objects.

Instead, each instance maintains its own local connection registry and uses Redis Pub/Sub to relay events to other instances.

## Project Structure

```text
src/
└── monopoly/
    ├── __init__.py
    ├── main.py          # FastAPI application entry point and Redis lifecycle
    ├── api_routes.py    # Room creation and joining endpoints
    ├── connection.py    # Redis room manager and WebSocket connection management
    ├── websocket.py     # WebSocket events and player actions
    ├── main_game.py     # Monopoly game engine and state serialization
    ├── player.py        # Player data and actions
    └── properties.py    # Board, properties, and tile behavior
```

## Using the Deployed Backend

### HTTP Endpoints

#### Create a Room

Creates a new game room and initializes its state in Redis.

**Request**

```http
POST /api/rooms/create
```

**Example**

```bash
curl -X POST https://monopoly-chi-lime.vercel.app/api/rooms/create
```

**Response example**

```json
{
  "success": true,
  "room_id": "your-room-id",
  "message": "Room initialized successfully."
}
```

The returned room ID is used by players when connecting through WebSockets.

#### Join a Room

Checks whether an existing room can be joined.

**Request**

```http
POST /api/rooms/join
```

**Request Body**

```json
{
  "room_code": "your-room-id"
}
```

**Example**

```bash
curl -X POST https://monopoly-chi-lime.vercel.app/api/rooms/join \
  -H "Content-Type: application/json" \
  -d '{"room_code":"your-room-id"}'
```

A successful response confirms that the room exists and is waiting for players. Players must still establish a WebSocket connection to participate.

## WebSocket

WebSockets provide real-time communication between players and the game server.

### Connecting to a Room

Use the following endpoint:

```text
wss://monopoly-chi-lime.vercel.app/ws/{room_id}?name={player_name}
```

Replace `your-room-id` with the room ID returned by the create-room endpoint.

### JavaScript Frontend Example

The browser's native `WebSocket` API can be used to connect to the deployed backend.

```javascript
const API_URL = "https://monopoly-chi-lime.vercel.app";

// Create a room
async function createRoom() {
  const response = await fetch(`${API_URL}/api/rooms/create`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to create room");
  }

  const data = await response.json();

  console.log("Created room:", data.room_id);

  return data.room_id;
}

// Join an existing room
async function joinRoom(roomCode) {
  const response = await fetch(`${API_URL}/api/rooms/join`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      room_code: roomCode,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to join room");
  }

  return await response.json();
}

// Connect to a room through WebSocket
function connectToRoom(roomId, playerName) {
  const ws = new WebSocket(
    `wss://monopoly-chi-lime.vercel.app/ws/${roomId}?name=${encodeURIComponent(playerName)}`,
  );

  ws.onopen = () => {
    console.log("Connected to game room!");
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    console.log("Received from server:", message);

    // Handle server events here
    // Example: update the game board or player information
  };

  ws.onclose = (event) => {
    console.log("Disconnected from server:", event.code);
  };

  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
  };

  return ws;
}

// Send a game action
function sendAction(ws, action, data = {}) {
  if (ws.readyState !== WebSocket.OPEN) {
    console.error("WebSocket is not connected");
    return;
  }

  ws.send(
    JSON.stringify({
      action,
      data,
    }),
  );
}

// Example usage
async function startGameSession() {
  try {
    const roomId = await createRoom();

    const ws = connectToRoom(roomId, "Alice");

    // Send actions after the WebSocket connection is established
    ws.addEventListener("open", () => {
      console.log("Ready to send game actions");

      // Example:
      // sendAction(ws, "START_GAME");
      // sendAction(ws, "ROLL_DICE");
    });

    return { roomId, ws };
  } catch (error) {
    console.error("Game session error:", error);
  }
}
```

**Note:** The example assumes the WebSocket handler accepts messages in the format:

```json
{
  "action": "ROLL_DICE",
  "data": {}
}
```

Adjust the message format to match the implementation in `websocket.py`.

### Terminal-Based WebSocket Testing

You can also connect using `wscat`.

**Alice:**

```bash
wscat -c "wss://monopoly-chi-lime.vercel.app/ws/your-room-id?name=Alice"
```

**Bob:**

```bash
wscat -c "wss://monopoly-chi-lime.vercel.app/ws/your-room-id?name=Bob"
```

Example message:

```json
{
  "action": "ROLL_DICE"
}
```

### WebSocket Actions

Actions are sent as JSON messages.

| Action             | Purpose                                               |
| ------------------ | ----------------------------------------------------- |
| `START_GAME`       | Starts the game                                       |
| `ROLL_DICE`        | Rolls the dice and moves the current player           |
| `BUY_PROPERTY`     | Purchases an available property                       |
| `DECLINE_PROPERTY` | Declines a property purchase                          |
| `END_TURN`         | Ends the current turn                                 |
| `FORFEIT`          | Forfeits and removes the current player from the game |

The server validates incoming actions, updates the game state, and broadcasts resulting events to connected players.

## Game Engine

The game logic is separated from the FastAPI and WebSocket layers.

- `main_game.py` handles turn management, dice rolls, player movement, game state serialization, and winner detection.
- `player.py` manages player information, money, and owned properties.
- `properties.py` defines board tiles, property prices, rent calculations, and tile behavior.

The game engine supports serialization and reconstruction of game state using `to_dict()` and `from_dict()`. This allows game state to be stored in Redis and restored when another server instance needs to process a player's action.

## Local Development

The deployed backend is the primary way to access the game. The following instructions are for running and testing the backend locally.

### Requirements

- Python 3.10 or later
- pip
- Redis connection URL (Upstash or another Redis instance)

### Installation

Clone the repository:

```bash
git clone https://github.com/jijahh/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

Navigate to the source directory:

```bash
cd src
```

Install the dependencies:

```bash
pip install -r ../requirements.txt
```

Alternatively, if using `uv`:

```bash
uv sync
```

### Environment Variables

Create a `.env` file in the project root:

```env
REDIS_URL=rediss://default:your-password@your-redis-host:6379
```

Replace the example value with your Redis database's actual connection URL.

**Important:** Never commit your `.env` file or expose your Redis credentials publicly.

### Running the Server

From the `src` directory, start the FastAPI application:

```bash
uvicorn monopoly.main:app --reload
```

The local server will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### Local WebSocket Connections

When testing locally, use `ws://` instead of `wss://`:

```bash
wscat -c "ws://127.0.0.1:8000/ws/your-room-id?name=Alice"
```

## Deployment Configuration

The backend is deployed on Vercel and uses Upstash Redis for shared state.

The following environment variable must be configured in the Vercel project settings:

| Variable    | Description                   |
| ----------- | ----------------------------- |
| `REDIS_URL` | Redis database connection URL |

The Redis connection URL should use the native Redis TCP connection format supported by the Python Redis client.

The application initializes its Redis connection during FastAPI startup and closes it during shutdown.

## Current Limitations

- Redis Pub/Sub messages are not persistent. If a server instance or subscriber disconnects, it may miss events published during that period.
- Game rooms have a configured expiration time in Redis and are not intended to persist indefinitely.
- A server restart or unexpected disconnection may require clients to reconnect and retrieve the latest game state.
- Authentication and player accounts are not currently implemented.
- Property upgrades and some special tile effects may not yet be fully implemented.

## Development Notes

When adding new features, keep responsibilities separated:

- Put game rules and turn logic in `main_game.py`.
- Put player-specific state and operations in `player.py`.
- Put board and tile behavior in `properties.py`.
- Handle incoming player actions and outgoing events in `websocket.py`.
- Manage Redis room state, connection tracking, and event distribution in `connection.py`.
- Keep application startup, shutdown, and Redis initialization in `main.py`.

This separation keeps the game engine independent of the networking layer and makes the backend easier to maintain and extend.
