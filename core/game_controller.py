from __future__ import annotations

from typing import Callable

from core.deck import Deck
from core.card import Card
from core import protocol as proto
import random

from logger import logger


class GameController:
    def __init__(self,
                 value_player: int,
                 nickname: str,
                 is_client: bool = True,
                 on_send: Callable[[bytes], None] | None = None,
                 on_close: Callable[[], None] | None = None):
        self.exit_nickname = None
        self._send = on_send
        self._close_net = on_close
        self.state_ready: Callable[[str], None] | None = None
        self.player_take_card = None
        self.winner_player = None
        self.step_player = None
        self.nicknames = None
        self.my_nickname = nickname
        self.is_client = is_client
        self.my_hands = {}
        self.is_my_step = False
        self.deck = Deck()
        self.hands = {}
        self.queue = []
        self.top_card = self.deck.pick_start_card()
        self.current = ""
        self.value_player = value_player
        if not self.is_client:
            self.value_player += 1

    def _dispatch(self, cmd: str) -> None:
        if self.state_ready:
            self.state_ready(cmd)

    def new_game(self, nicknames):
        random.shuffle(self.deck.cards)
        self.nicknames = nicknames
        self.hands = self.deck.deal_cards(nicknames)

        self.queue = nicknames[:]
        random.shuffle(self.queue)
        self.current = self.queue[0]
        self.is_my_step = self.my_nickname == self.current
        msg = proto.start_game(
            top=self.top_card,
            queue=self.queue,
            hands=self.hands,
            deck=self.deck.cards,
            nicknames=self.nicknames
        )

        self.my_hands = {
            nickname: [Card.from_dict(c) for c in cards]
            for nickname, cards in msg.get("players", {}).items()
        }.get(self.my_nickname, [])

        if self._send:
            self._send(proto.dumps(msg))

        self._dispatch("start_game")

    def play_card(self, card: Card):
        if card in self.my_hands:
            self.my_hands.remove(card)
        self.top_card = card

        if card.action == "reverse":
            if len(self.queue) == 2:
                self.current = self.my_nickname
            else:
                self.queue.reverse()
                self.current = self._next_player()
        elif card.action == "skip":
            self.current = self._next_player()
            self.current = self._next_player()
        else:
            self.current = self._next_player()

        if self._send:
            self._send(proto.dumps(proto.step(self.my_nickname, card, self.current)))
        if len(self.my_hands) == 0:
            self.win()

    def win(self):
        if self._send:
            self._send(proto.dumps(proto.end_game(self.my_nickname)))
        self.end_game(proto.end_game(self.my_nickname))

    def draw_one(self):
        card = self.deck.draw_card()
        self.my_hands.append(card)
        if self._send:
            self._send(proto.dumps(proto.take_card(self.my_nickname, card)))
        return card

    def _next_player(self):
        idx = (self.queue.index(self.current) + 1) % len(self.queue)
        return self.queue[idx]

    def handle_command(self, data):
        if data["command"] == "start_game":
            self.handle_start_game(data)
            return self.value_player
        elif data["command"] == "step":
            self.handle_step(data)
        elif data["command"] == "take_card":
            self.handle_take_card(data)
        elif data["command"] == "end_game":
            self.end_game(data)

    def handle_start_game(self, data):
        self.value_player = data.get("value_numbers")
        self.queue = data.get("queue_players")
        self.current = data.get("current_player")
        self.top_card = Card.from_dict(data.get("top_card"))
        logger.info(self.my_nickname)
        self.is_my_step = self.my_nickname == self.current
        self.deck = Deck()
        self.deck.cards = [Card.from_dict(c) for c in data.get("deck", [])]

        self.hands = None
        self.nicknames = data.get("nicknames")
        self.my_hands = {
            nickname: [Card.from_dict(c) for c in cards]
            for nickname, cards in data.get("players", {}).items()
        }.get(self.my_nickname, [])

    def __str__(self) -> str:
        return (
            f"GameController:\n"
            f"  My Nickname: {self.my_nickname}\n"
            f"  is_my_step: {self.is_my_step}\n"
            f"  Value Player: {self.value_player}\n"
            f"  Current Player: {self.current}\n"
            f"  Queue: {self.queue}\n"
            f"  Top Card: {self.top_card}\n"
            f"  my_hands:\n{self.my_hands}\n"
            f"  Deck: {len(self.deck.cards)} cards remaining"
        )

    def handle_step(self, data):
        self.top_card = Card.from_dict(data.get("top_card"))
        self.current = data.get("next_player")
        self.is_my_step = self.my_nickname == self.current
        self.step_player = data.get("player")
        result_command = "step" if not self.top_card.action else self.top_card.action
        self._dispatch(result_command)

    def end_game(self, data):
        self.winner_player = data.get("winner")
        self._dispatch("end_game")

    def handle_take_card(self, data):
        self.player_take_card = data.get("player")
        card_dict = data["card"]
        card = Card.from_dict(card_dict)
        self.deck.pop_card(card)
        self._dispatch("take_card")

    def close_game(self):
        if self._close_net:
            self._close_net()

    def handle_error(self, nickname: str | None = None):
        self.exit_nickname = nickname
        self._dispatch("error")
