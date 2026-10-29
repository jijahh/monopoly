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
    "Shenzhen": [18, 90, 240, 680, 850, 1000],
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
tax_amount = {
    "Earnings Tax": lambda player: math.floor(player.money * 0.10),
    "Premium Tax": lambda player: 75,
}

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

treasure_cards = [
    "Happy holidays - receive 20",
    "From trading stocks you earned $50.",
    "You received $100 from your sibling.",
    "Advance to Start.",
    "Go to prison.",
    "From gift cards you get $100.",
    "You found a wallet containing some cash. Collect $200.",
    "You have won third prize in a lottery. Collect $15.",
    "It's time to renovate your properties. Pay $30 per house and $120 per hotel you own.",
    "Beneficial business decisions. You made a profit of $25.",
    "Tax refund. Collect $100.",
    "Your phone died. Pay $50 for a repair",
    "Got a Pardon card from the treasures stack",
    "You host a party. Collect $50 from every player for equipment.",
    "Your car has ran out of gas. Pay $50.",
    "Happy birthday! Collect $10 from every player.",
    "Car rental insurance. Pay $60 ",
]
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

    def calculate_rent(self, game):
        rents = property_rent[self.name]

        if isinstance(self, UtilityProperty):
            utilities_owned = sum(
                isinstance(p, UtilityProperty) for p in self.owner.owned_properties
            )

            rent_function = rents[min(utilities_owned - 1, len(rents) - 1)]

            return rent_function(sum(game.last_roll))

        if isinstance(self, Airport):
            airports_owned = sum(
                isinstance(p, Airport) for p in self.owner.owned_properties
            )

            return rents[min(airports_owned - 1, len(rents) - 1)]

        # Cities: the rent table represents base rent,
        # increasing house levels and the hotel level.
        return rents[min(self.houses, len(rents) - 1)]

    def buy_property(self, player):
        pass

    def land_on(self, player, game):
        """Resolve landing without terminal input so the WebSocket layer can decide."""
        if self.owner is None:
            # The client must explicitly send BUY_PROPERTY or DECLINE_PROPERTY.
            if player.money >= self.price:
                game.pending_purchase = {"player_name": player.name, "tile": self}
        elif self.owner is not player:
            rent = self.calculate_rent(game)
            player.get_taxed(rent)
            self.owner.get_paid(rent)


class Cities(Property):
    def __init__(self, name, price, country):
        super().__init__(name, price)
        self.country = country


class Airport(Property):
    pass


class UtilityProperty(Property):
    pass


class Tax(Tile):
    def land_on(self, player, game):
        amount = tax_amount[self.name](player)
        print(f"{player.name} pays ${amount} in tax.")
        player.get_taxed(amount)


class Treasure(Tile):
    def land_on(self, player, game):
        card = random.choice(treasure_cards)
        print(card)

        if card in easy_treasure:
            amount = easy_treasure[card]

            if amount >= 0:
                player.get_paid(amount)
            else:
                player.get_taxed(-amount)


class Surprise(Tile):
    def land_on(self, player, game):
        print("Surprise cards are not implemented yet.")


class Unique(Tile):
    def __init__(self, name):
        super().__init__(name)

    def land_on(self, player, game):
        if self.name == "Start":
            pass
        elif self.name == "Prison":
            pass
        elif self.name == "Vacation":
            player.on_vacation += 2
            return
        elif self.name == "Go To Prison":
            player.position = board.index("Prison")
            player.in_prison += 3


class Board:
    def __init__(self):
        self.board = [self.create_tile(name) for name in board]

    def create_tile(self, name):
        if name in city_mapping:
            return Cities(
                name,
                property_prices[name],
                city_mapping[name],
            )

        if name in airports:
            return Airport(name, property_prices[name])

        if name in utilities:
            return UtilityProperty(name, property_prices[name])

        if name in taxes:
            return Tax(name)

        if name == "Treasure":
            return Treasure(name)

        if name == "Surprise":
            return Surprise(name)

        return Unique(name)
