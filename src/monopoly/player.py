from .properties import *


class Player:
    def __init__(self, name, player_no, money=1500):
        self.name = name
        self.player_no = player_no
        self.position = 0
        self.owned_cities = []
        self.owned_airport = []
        self.owned_utitilities = []
        self.owned_properties = []
        self.houses = 0
        self.hotels = 0
        self.money = money
        self.in_prison = 0
        self.on_vacation = 0
        self.pardons = 0
        self.can_end = False
        self.can_roll = True

    def move(self):
        if self.on_vacation or self.in_prison:
            self.can_roll = False
        if self.on_vacation:
            self.on_vacation -= 1
        if self.in_prison:
            choice = self.pay_bail()
            if choice:
                return "end_turn"
            else:
                return "roll_out_of_prison"
        choice = (
            input("What is your move? (roll_dice, end_turn, upgrade_property): ")
            .strip()
            .lower()
        )
        if choice == "upgrade_property":
            pass
        elif choice == "end_turn":
            if self.can_end:
                self.can_end = False
                self.can_roll = True
                return choice
            else:
                print("Can't end, must roll dice first")
        elif choice == "roll_dice":
            if self.can_roll:
                print("Already rolled dice")
            else:
                self.can_roll = True
                self.can_end = False
                return choice

    def pay_bail(self):
        if money < 50:
            print("No money for bail")
            return False
        choice = ""
        while not choice or choice not in ("yes", "no"):
            choice = input("Pay bail? (yes/no): ").strip().lower()
            if choice not in ("yes", "no"):
                print(f"Choice {choice} must be 'yes' or 'no'")
        if choice == "yes":
            money -= 50
            self.in_prison = 0
        return True if choice == "yes" else False

    def buy_property(self, property):
        self.money -= property.price
        self.owned_properties.append(property)
        if type(property) == Cities:
            self.owned_cities.append(property)
        elif type(property) == Airport:
            self.owned_airport.append(property)
        elif type(property) == UtilityProperty:
            self.owned_utitilities.append(property)

    def get_taxed(self, amount):
        self.money -= amount

    def get_paid(self, amount):
        self.money += amount

    def get_easy_treasure(self, amount):
        self.money += amount
