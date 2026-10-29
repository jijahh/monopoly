from monopoly.properties import *


class Player:
    def __init__(self, name, player_no, money=1500):
        self.name = name
        self.player_no = player_no
        self.position = 0
        self.owned_cities = []
        self.owned_airport = []
        self.owned_utilities = []
        self.owned_properties = []
        self.houses = 0
        self.hotels = 0
        self.money = money
        self.in_prison = 0
        self.on_vacation = 0
        self.pardons = 0
        self.has_rolled = False

    # def pay_bail(self):
    #     if self.money < 50:
    #         print("Not enough money for bail.")
    #         return False

    #     choice = ""

    #     while choice not in ("yes", "no"):
    #         choice = input("Pay bail? (yes/no): ").strip().lower()

    #     if choice == "yes":
    #         self.money -= 50
    #         self.in_prison = 0
    #         return True

    #     return False

    def buy_property(self, tile):
        if tile.owner is not None:
            return False

        if self.money < tile.price:
            print("Not enough money to buy this property.")
            return False

        self.money -= tile.price
        tile.owner = self
        self.owned_properties.append(tile)

        if isinstance(tile, Cities):
            self.owned_cities.append(tile)

        elif isinstance(tile, Airport):
            self.owned_airport.append(tile)

        elif isinstance(tile, UtilityProperty):
            self.owned_utilities.append(tile)

        return True

    def get_taxed(self, amount):
        self.money -= amount

    def get_paid(self, amount):
        self.money += amount

    def get_easy_treasure(self, amount):
        self.money += amount
