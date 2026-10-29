import random
from monopoly.player import Player
from monopoly.properties import Board, Property


class Game:
    def __init__(self, player_names):
        names = [name.strip() for name in player_names if name and name.strip()]
        if len(names) < 2:
            raise ValueError("At least two players are required.")
        if len({name.casefold() for name in names}) != len(names):
            raise ValueError("Player names must be unique within a room.")

        random.shuffle(names)
        self.players = [Player(name, i) for i, name in enumerate(names)]
        self.player_to_play = 0
        self.board = Board()
        self.winner = None
        self.last_roll = (0, 0)
        self.pending_purchase = None

    @property
    def current_player(self):
        return self.players[self.player_to_play]

    def roll_dice(self):
        return (random.randint(1, 6), random.randint(1, 6))

    def move_player(self, player, steps):
        board_size = len(self.board.board)
        raw_position = player.position + steps

        if raw_position >= board_size:
            player.get_paid(300 if raw_position == board_size else 200)

        player.position = raw_position % board_size
        self.board.board[player.position].land_on(player, self)

    def handle_action(self, player_name, action, data=None):
        if self.winner is not None:
            raise ValueError("The game has already ended.")

        player = self.current_player
        if player.name != player_name:
            raise ValueError("It is not your turn.")

        action = action.strip().upper()
        events = []

        if action == "ROLL_DICE":
            if player.has_rolled:
                raise ValueError("You have already rolled this turn.")
            if self.pending_purchase is not None:
                raise ValueError("Resolve the property purchase first.")

            player.has_rolled = True
            self.last_roll = self.roll_dice()
            total = sum(self.last_roll)
            self.move_player(player, total)
            events.append(
                {
                    "type": "DICE_ROLLED",
                    "player_name": player.name,
                    "rolls": list(self.last_roll),
                    "total": total,
                    "position": player.position,
                }
            )

            if self.pending_purchase is not None:
                tile = self.pending_purchase["tile"]
                events.append(
                    {
                        "type": "PROPERTY_PURCHASE_OFFERED",
                        "player_name": player.name,
                        "property": tile.name,
                        "price": tile.price,
                    }
                )
            events.append(self._state_event())
            return events

        if action in ("BUY_PROPERTY", "DECLINE_PROPERTY"):
            pending = self.pending_purchase
            if pending is None or pending["player_name"] != player.name:
                raise ValueError(
                    "There is no property purchase awaiting your decision."
                )

            tile = pending["tile"]
            self.pending_purchase = None
            if action == "BUY_PROPERTY":
                if not player.buy_property(tile):
                    raise ValueError("You cannot buy this property.")
                events.append(
                    {
                        "type": "PROPERTY_PURCHASED",
                        "player_name": player.name,
                        "property": tile.name,
                        "price": tile.price,
                    }
                )
            else:
                events.append(
                    {
                        "type": "PROPERTY_DECLINED",
                        "player_name": player.name,
                        "property": tile.name,
                    }
                )
            events.append(self._state_event())
            return events

        if action == "FORFEIT":
            self.players.pop(self.player_to_play)
            event = self.check_winner()
            if event:
                events.append(event)
                return events
            previous_player = player.name
            skipped = self._advance_to_next_active_player()
            events.append(
                {
                    "type": "TURN_CHANGED",
                    "previous_player": previous_player,
                    "current_player": self.current_player.name,
                    "skipped_players": skipped,
                }
            )
            events.append(self._state_event())
            return events
        if action == "END_TURN":
            if not player.has_rolled:
                raise ValueError("You must roll before ending your turn.")
            if self.pending_purchase is not None:
                raise ValueError("Buy or decline the property before ending your turn.")

            previous_player = player.name
            skipped = self._advance_to_next_active_player()
            events.append(
                {
                    "type": "TURN_CHANGED",
                    "previous_player": previous_player,
                    "current_player": self.current_player.name,
                    "skipped_players": skipped,
                }
            )
            events.append(self._state_event())
            return events

        raise ValueError(f"Unsupported action: {action}")

    def check_winner(self, reason=None):
        if self.winner is None and len(self.players) == 1:
            self.winner = self.players[0]
            self.player_to_play = 0
            self.pending_purchase = None

            event = {
                "type": "GAME_OVER",
                "winner": self.winner.name,
                "message": f"{self.winner.name} wins the game!",
            }
            if reason:
                event["reason"] = reason
            self._pending_events.append(event)
        return self.winner

    def _advance_to_next_active_player(self):
        """Advance turn and apply the engine's existing skip-turn counters."""
        skipped = []
        attempts = 0
        max_attempts = max(1, len(self.players) * 10)

        while attempts < max_attempts:
            attempts += 1
            self.player_to_play = (self.player_to_play + 1) % len(self.players)
            player = self.current_player
            player.has_rolled = False

            if player.on_vacation > 0:
                player.on_vacation -= 1
                skipped.append({"player_name": player.name, "reason": "vacation"})
                continue
            if player.in_prison > 0:
                player.in_prison -= 1
                skipped.append({"player_name": player.name, "reason": "prison"})
                continue
            return skipped

        raise RuntimeError("Could not find an active player; check skip-turn counters.")

    def _state_event(self):
        return {"type": "GAME_STATE", "state": self.to_dict()}

    def to_dict(self):
        players = []
        for player in self.players:
            players.append(
                {
                    "name": player.name,
                    "player_no": player.player_no,
                    "position": player.position,
                    "money": player.money,
                    "owned_properties": [tile.name for tile in player.owned_properties],
                    "in_prison": player.in_prison,
                    "on_vacation": player.on_vacation,
                    "has_rolled": player.has_rolled,
                }
            )

        board = []
        for index, tile in enumerate(self.board.board):
            tile_state = {
                "index": index,
                "name": tile.name,
                "kind": type(tile).__name__,
            }
            if isinstance(tile, Property):
                tile_state.update(
                    {
                        "price": tile.price,
                        "owner": tile.owner.name if tile.owner else None,
                        "houses": tile.houses,
                    }
                )
                if hasattr(tile, "country"):
                    tile_state["country"] = tile.country
            board.append(tile_state)

        pending = None
        if self.pending_purchase is not None:
            tile = self.pending_purchase["tile"]
            pending = {
                "player_name": self.pending_purchase["player_name"],
                "property": tile.name,
                "price": tile.price,
            }

        return {
            "status": "finished" if self.winner else "playing",
            "current_player": self.current_player.name if self.players else None,
            "last_roll": list(self.last_roll),
            "winner": self.winner.name if self.winner else None,
            "players": players,
            "board": board,
            "pending_purchase": pending,
        }
