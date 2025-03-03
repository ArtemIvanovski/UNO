import random

from core.card import Card


class Deck:
    def __init__(self):
        self.cards = self.generate_deck()
        self.shuffle()

    def generate_deck(self):
        colors = ["red", "blue", "green", "yellow"]
        values = [str(i) for i in range(10)]  # 0-9
        action_cards = ["skip", "reverse", "draw two"]
        wild_cards = ["wild", "draw four"]

        deck = []

        for color in colors:
            deck.append(Card(color, "0"))
            for value in values[1:]:
                deck.append(Card(color, value))
                deck.append(Card(color, value))

            for action in action_cards:
                deck.append(Card(color, action, action))
                deck.append(Card(color, action, action))

        # Wild-карты (по 4 каждого типа)
        for _ in range(4):
            deck.append(Card("black", "wild", "wild"))
            deck.append(Card("black", "draw four", "draw four"))

        return deck

    def shuffle(self):
        """
        Перемешивает колоду.
        """
        random.shuffle(self.cards)

    def draw_card(self):
        """
        Берет одну карту из колоды.
        """
        return self.cards.pop() if self.cards else None

    def deal_cards(self, num_players):
        """
        Раздает по 7 карт каждому игроку.
        :param num_players: Количество игроков
        :return: Список списков карт для каждого игрока
        """
        hands = [[] for _ in range(num_players)]
        for _ in range(7):  # Раздаем по 7 карт
            for hand in hands:
                hand.append(self.draw_card())
        return hands

    def __repr__(self):
        return f"Deck({len(self.cards)} карт)"
