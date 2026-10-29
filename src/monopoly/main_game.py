import random
from .properties import Board
from enum import Enum
from .player import Player


class Game:
    def __init__(self, player_names):
        players = []
        for i in range(len(player_names)):
            player = random.choice(player_names)
            player_names.remove(player)
            players.append(Player(player, i))
        self.players = players
        self.player_to_play = 0
        self.board = Board()
        self.winner = None

    def move(self):
        current_player = self.players[self.player_to_play]
        choice = ""
        while choice != "end_turn":
            choice = current_player.move()
            if choice == "roll_dice":
                dice_roll = sum(self.roll_dice())
                raw_move = current_player.position + dice_roll
                if raw_move > len(self.board.board):
                    current_player.get_easy_treasure(200)
                current_player.position = raw_move % len(self.board.board)
                self.board.board[current_player.position].land_on(current_player, self)
            elif choice == "roll_out_of_prison":
                dice_roll_1, dice_roll_2 = self.roll_dice
                if dice_roll_1 == dice_roll_2:
                    raw_move = current_player.position + dice_roll
                    if raw_move > len(self.board.board):
                        current_player.get_easy_treasure(200)
                    current_player.position = raw_move % len(self.board.board)
                    self.board.board[current_player.position].land_on(
                        current_player, self
                    )
                break
            self.player_to_play = (self.player_to_play + 1) % len(self.players)

    def roll_dice(self):
        dice_roll_1 = random.randint(1, 6)
        dice_roll_2 = random.randint(1, 6)
        print(f"Rolled dice! : {dice_roll_1}, {dice_roll_2}")
        return (dice_roll_1, dice_roll_2)

    def draw_board(self):
        player_pos = {}
        for player in self.players:
            if player.position in player_pos:
                player_pos[player.position].append(player.name)
            else:
                player_pos[player.position] = [player.name]
        for index, tile in enumerate(self.board.board):
            if index in player_pos:
                print(str(tile) + str(player_pos[index]))
            else:
                print(tile)

    def game_loop(self):
        self.draw_board()
        self.move()
        self.player_to_play = (self.player_to_play + 1) % len(self.players)


game = Game(["jijah", "mycronare"])
while True:
    game.game_loop()


def main() -> None:
    print("Hello from monopoly!")
