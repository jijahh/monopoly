from abc import ABC, abstractmethod
import random
import math

property_prices = {
    "Salvador": 60,
    "Rio": 60,
    "TLV Airport": 200,
    "Tel Aviv": 100,
    "Haifa": 110,
    "Jerusalem": 120,
    "Venice": 130,
    "Power Company": 150,
    "Milan": 140,
    "Rome": 160,
    "MUC Airport": 200,
    "Frankfurt": 180,
    "Munich": 190,
    "Berlin": 200,
    "Shenzhen": 210,
    "Beijing": 220,
    "Shanghai": 240,
    "CDG Airport": 200,
    "Lyon": 260,
    "Water Company": 150,
    "Toulouse": 270,
    "Paris": 280,
    "Liverpool": 290,
    "Manchester": 300,
    "London": 320,
    "JFK Airport": 200,
    "San Francisco": 360,
    "New York": 400,
}
property_rent = {
    "Salvador": [2, 10, 30, 90, 150, 240],
    "Rio": [4, 20, 60, 190, 330, 460],
    "TLV Airport": [25, 50, 100, 200],
    "Tel Aviv": [6, 30, 90, 260, 380, 540],
    "Haifa": [6, 30, 90, 280, 400, 560],
    "Jerusalem": [8, 40, 110, 300, 460, 610],
    "Venice": [10, 50, 140, 440, 600, 740],
    "Power Company": [lambda x: x * 4, lambda x: x * 10],
    "Milan": [10, 50, 160, 460, 630, 760],
    "Rome": [12, 60, 180, 500, 700, 900],
    "MUC Airport": [25, 50, 100, 200],
    "Frankfurt": [14, 70, 190, 540, 760, 950],
    "Munich": [15, 70, 210, 560, 760, 960],
    "Berlin": [15, 80, 220, 600, 780, 1000],
    "Shenzen": [18, 90, 240, 680, 850, 1000],
    "Beijing": [20, 90, 260, 710, 900, 1000],
    "Shanghai": [20, 100, 290, 740, 920, 1100],
    "CDG Airport": [25, 50, 100, 200],
    "Lyon": [20, 100, 320, 800, 950, 1100],
    "Water Company": [lambda x: x * 4, lambda x: x * 10],
    "Toulouse": [20, 120, 350, 825, 1000, 1150],
    "Paris": [25, 120, 350, 850, 1000, 1200],
    "Liverpool": [25, 120, 380, 850, 1050, 1250],
    "Manchester": [26, 140, 400, 950, 1150, 1300],
    "London": [30, 140, 440, 1000, 1200, 1400],
    "JFK Airport": [25, 50, 100, 200],
    "San Francisco": [35, 180, 550, 1150, 1350, 1525],
    "New York": [50, 200, 600, 1400, 1700, 2000],
}
tax_amount = {"Earnings Tax": lambda x: math.floor(x * 0.10), "Premium Tax": 75}

board = [
    "Start",
    "Salvador",
    "Treasure",
    "Rio",
    "Earnings Tax",
    "TLV Airport",
    "Tel Aviv",
    "Haifa",
    "Surprise",
    "Jerusalem",
    "Prison",
    "Venice",
    "Power Company",
    "Milan",
    "Rome",
    "MUC Airport",
    "Frankfurt",
    "Treasure",
    "Munich",
    "Berlin",
    "Vacation",
    "Shenzhen",
    "Surprise",
    "Beijing",
    "Shanghai",
    "CDG Airport",
    "Lyon",
    "Water Company",
    "Toulouse",
    "Paris",
    "Go To Prison",
    "Liverpool",
    "Manchester",
    "Treasure",
    "London",
    "JFK Airport",
    "Surprise",
    "San Francisco",
    "Premium Tax",
    "New York",
]
city_mapping = {
    "Salvador": "Brazil",
    "Rio": "Brazil",
    "Tel Aviv": "Israel",
    "Haifa": "Israel",
    "Jerusalem": "Israel",
    "Venice": "Italy",
    "Milan": "Italy",
    "Rome": "Italy",
    "Frankfurt": "Germany",
    "Munich": "Germany",
    "Berlin": "Germany",
    "Shenzhen": "China",
    "Beijing": "China",
    "Shanghai": "China",
    "Lyon": "France",
    "Toulouse": "France",
    "Paris": "France",
    "Liverpool": "England",
    "Manchester": "England",
    "London": "England",
    "San Francisco": "USA",
    "New York": "USA",
}
country_mapping = {
    "Brazil": ["Salvador, Rio"],
    "Israel": ["Tel Aviv", "Haifa", "Jerusalem"],
    "Italy": ["Venice", "Milan", "Rome"],
    "Germany": ["Munich", "Berlin"],
    "China": ["Shenzhen", "Beijing", "Shanghai"],
    "France": ["Lyon", "Toulose", "Paris"],
    "England": ["Liverpool", "Manchester", "London"],
    "USA": ["San Francisco", "New York"],
}
utilities = {"Power Company", "Water Company"}
airports = {"TLV Airport", "MUC Airport", "CDG Airport", "JFK Airport"}
taxes = {"Earnings Tax", "Premium Tax"}
special_tiles = {"Prison", "Vacation", "Go To Prison", "Start"}
treasure_cards = {
    "Happy holidays - receive 20"
    "From trading stocks you earned $50."
    "You received $100 from your sibling."
    "Advance to Start."
    "Go to prison."
    "From gift cards you get $100."
    "You found a wallet containing some cash. Collect $200."
    "You have won third prize in a lottery. Collect $15."
    "It's time to renovate your properties. Pay $30 per house and $120 per hotel you own."
    "Beneficial business decisions. You made a profit of $25."
    "Tax refund. Collect $100."
    "Your phone died. Pay $50 for a repair"
    "Got a Pardon card from the treasures stack"
    "You host a party. Collect $50 from every player for equipment."
    "Your car has ran out of gas. Pay $50."
    "Happy birthday! Collect $10 from every player."
    "Car rental insurance. Pay $60 "
}
easy_treasure = {
    "Happy holidays - receive 20": 20,
    "From trading stocks you earned $50.": 50,
    "You received $100 from your sibling.": 100,
    "From gift cards you get $100.": 100,
    "You found a wallet containing some cash. Collect $200.": 200,
    "You have won third prize in a lottery. Collect $15.": 15,
    "Beneficial business decisions. You made a profit of $25.": 25,
    "Tax refund. Collect $100.": 100,
    "Your phone died. Pay $50 for a repair": -50,
    "Your car has ran out of gas. Pay $50.": -50,
    "Happy birthday! Collect $10 from every player.": 0,
    "Car rental insurance. Pay $60 ": -60,
}


class Tile(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def land_on(self, player, game):
        pass

    def __str__(self):
        return self.name


class Property(Tile):
    def __init__(self, name, price):
        super().__init__(name)
        self.owner = None
        self.price = price
        self.houses = 0

    def buy_property(self, player):
        pass

    def land_on(self, player, game):
        choice = ""
        if self.owner == None:
            choice = input("Buy property? (yes, no)")
            if choice == "yes":
                if player.money > self.price:
                    self.owner = player
                    player.buy_property(self)
        elif self.owner == player:
            pass
        else:
            rent = property_rent[self.name][0]
            player.get_taxed(rent)
            self.owner.get_paid(rent)


class Cities(Property):
    def __init__(self, name, price, country):
        super().__init__(name, price)
        self.country = country


class Airport(Property):
    def __init__(self, name, price):
        super().__init__(name, price)


class UtilityProperty(Property):
    def __init__(self, name, price):
        super().__init__(name, price)


class Tax(Tile):
    def __init__(self, name):
        super().__init__(name)

    def land_on(self, player, game):
        amount = tax_amount[self.name]
        player.get_taxed(amount)


class Treasure(Tile):
    def __init__(self, name):
        super().__init__(name)

    def land_on(self, player, game):
        card = random.choice(treasure_cards)
        if card in easy_treasure:
            player.get_easy_treasure(easy_treasure[card])
        elif card:
            pass


class Surprise(Tile):
    def __init__(self, name):
        super().__init__(name)


class Unique(Tile):
    def __init__(self, name):
        super().__init__(name)

    def land_on(self, player, game):
        if self.name == "Start":
            player.get_easy_treasure(300)
        elif self.name == "Prison":
            pass
        elif self.name == "Vacation":
            player.on_vacation += 2
            return
        elif self.name == "Go To Prison":
            player.position = board.index("Go To Prison")
            player.in_prison += 3


class Board:
    def __init__(self):
        board_list = []
        for tile in board:
            if tile in city_mapping:
                board_list.append(
                    Cities(tile, property_prices[tile], city_mapping[tile])
                )
            elif tile in airports:
                board_list.append(Airport(tile, property_prices[tile]))
            elif tile in utilities:
                board_list.append(UtilityProperty(tile, property_prices[tile]))
            elif tile in taxes:
                board_list.append(Tax(tile))
            else:
                board_list.append(Unique(tile))
        self.board = board_list

    def draw(self):
        for tile in self.board:
            print(tile)
