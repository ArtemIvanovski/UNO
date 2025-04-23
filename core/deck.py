import random
from typing import List

from core.card import Card
from logger import logger

COLORS = ["red", "blue", "green", "yellow"]
NUMBERS = [str(i) for i in range(10)]
ACTIONS_COLOR = ["skip", "reverse", "draw two"]
ACTIONS_WILD = ["wild", "draw four"]


class Deck:

    def __init__(self) -> None:
        self.cards: List[Card] = self._build()

    def _build(self) -> List[Card]:
        deck: List[Card] = []

        for col in COLORS:
            deck.append(Card(col, "0"))
            for num in NUMBERS[1:]:
                deck.extend([Card(col, num)] * 2)

            for act in ACTIONS_COLOR:
                deck.extend([Card(col, act, act)] * 2)

        for _ in range(4):
            deck.append(Card("black", "wild", "wild"))
            deck.append(Card("black", "draw four", "draw four"))

        random.shuffle(deck)
        return deck

    def draw_card(self) -> Card:
        card = self.cards.pop()
        logger.info(f"Карта из колоды {card}")
        logger.info(f"Колво карт в колоде {len(self.cards)}")
        return card

    def pop_card(self, card: Card):
        for idx, c in enumerate(self.cards):
            if (c.color, c.value, c.action) == (card.color, card.value, card.action):
                return self.cards.pop(idx)
        logger.error(f"Не удалось найти карту в колоде: {card}")

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_cards(self, nicknames: list[str], hand_size: int = 7) -> dict[str, list[Card]]:
        return {nickname: [self.draw_card() for _ in range(hand_size)] for nickname in nicknames}

    def pick_start_card(self) -> Card:
        for idx, c in enumerate(self.cards):
            if c.color != "black" and c.value.isdigit():
                return self.cards.pop(idx)
        return self.draw_card()

    def __len__(self) -> int:
        return len(self.cards)
