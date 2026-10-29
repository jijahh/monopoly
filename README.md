# Monopoly Game Backend

A multiplayer Monopoly game backend built with Python and FastAPI. It provides HTTP endpoints for room management and WebSocket communication for real-time game updates.

## Tech Stack

- Python
- FastAPI
- Uvicorn
- WebSockets

## Project Structure

```text
src/
└── monopoly/
    ├── __init__.py
    ├── main.py          # FastAPI application entry point
    ├── api_routes.py    # Room creation and joining endpoints
    ├── connection.py    # WebSocket connection management
    ├── websocket.py     # WebSocket events and player actions
    ├── main_game.py     # Monopoly game engine
    ├── player.py        # Player data and actions
    └── properties.py    # Board, properties, and tile behavior
```

## Deployment

The API is deployed on Vercel:

**Base URL:** https://monopoly-chi-lime.vercel.app/
**Interactive Docs:** https://monopoly-chi-lime.vercel.app/docs

The root endpoint can be used to check whether the API is responding.

### WebSocket Connection

Use the deployed server URL when connecting to the API from a client. The WebSocket endpoint and its supported message format should match the implementation in `websocket.py`.

For local development, run the server using:

```bash
uvicorn monopoly.main:app --reload
```

## Getting Started

### Requirements

- Python 3.10 or later
- pip

### Installation

Navigate to the project directory:

```bash
cd src
```

Install the dependencies:

```bash
pip install fastapi "uvicorn[standard]"
```

### Running the Server

Start the FastAPI application from the `src` directory:

```bash
uvicorn monopoly.main:app --reload
```

The server will run at:

```text
http://127.0.0.1:8000
```

The interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## HTTP Endpoints

### Create a Room

Creates a room and returns its room ID.

**Request**

```http
POST /api/rooms/create
```

**Example**

```bash
curl -X POST http://127.0.0.1:8000/api/rooms/create
```

The response contains a room ID that players use to connect to the same game.

### Join a Room

Checks whether a room exists.

**Request**

```http
POST /api/rooms/join
```

**Request body**

```json
{
  "room_code": "your-room-id"
}
```

**Example**

```bash
curl -X POST http://127.0.0.1:8000/api/rooms/join \
  -H "Content-Type: application/json" \
  -d '{"room_code":"your-room-id"}'
```

Players must connect through the WebSocket endpoint to participate in the game.

## WebSocket

The WebSocket endpoint allows players to connect to a room and exchange real-time messages.

### Connecting to a Room

```text
ws://127.0.0.1:8000/ws/{room_id}?name={player_name}
```

Example:

```bash
wscat -c "ws://127.0.0.1:8000/ws/your-room-id?name=Alice"
```

Connect another player using a separate terminal:

```bash
wscat -c "ws://127.0.0.1:8000/ws/your-room-id?name=Bob"
```

Replace `your-room-id` with the room ID returned by the create-room endpoint.

### WebSocket Actions

Actions are sent as JSON messages.

The intended game actions include:

| Action             | Purpose                                   |
| ------------------ | ----------------------------------------- |
| `START_GAME`       | Start the game                            |
| `ROLL_DICE`        | Roll the dice and move the current player |
| `BUY_PROPERTY`     | Purchase an available property            |
| `DECLINE_PROPERTY` | Decline a property purchase               |
| `END_TURN`         | End the current turn                      |
| `FORFEIT`          | Leave the game by forfeiting              |

Example message:

```json
{
  "action": "ROLL_DICE"
}
```

The server should validate each action, update the game state, and broadcast the resulting events to connected players.

**Note:** These actions must be implemented and connected to the game engine in `websocket.py` before they can all be used. The WebSocket handler and room manager must also share a consistent room data structure.

## Game Engine

The game logic is separated from the FastAPI application.

- `main_game.py` manages turns, dice rolls, player movement, and winner detection.
- `player.py` stores player information, money, and owned properties.
- `properties.py` defines the board tiles, property prices, rent calculations, and tile effects.

Keeping the game engine separate from the WebSocket layer makes it easier to test game rules independently of the network connection.

## Current Limitations

- The game state is stored in memory and is lost when the server restarts.
- Property upgrades and some special tile effects are not fully implemented.
- Player elimination and winner detection depend on the game engine being connected to the WebSocket action flow.
- Room creation, joining, and WebSocket connections must use the same room manager structure.
- Authentication and persistent storage are not currently included.

## Development Notes

When adding new game features, keep the responsibilities separated:

- Put game rules in `main_game.py`.
- Put player-specific state and operations in `player.py`.
- Put board and tile behavior in `properties.py`.
- Handle incoming player actions and outgoing events in `websocket.py`.
- Keep room membership and connections in `connection.py`.

This structure keeps the game logic independent from the transport layer and makes the backend easier to maintain.
