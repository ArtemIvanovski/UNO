import json
from typing import Dict, List
from core.card import Card


def _card_dict(c: Card) -> Dict:
    return {"color": c.color, "value": c.value, "action": c.action}


def start_game(top: Card,
               queue: List[str],
               hands: Dict[str, List[Card]],
               deck: List[Card],
               nicknames: List[str]) -> Dict:
    return {
        "command": "start_game",
        "value_numbers": len(queue),
        "queue_players": queue,
        "current_player": queue[0],
        "top_card": _card_dict(top),
        "deck": [_card_dict(c) for c in deck],
        "players": {n: [_card_dict(c)
                        for c in hand]
                    for n, hand in hands.items()},
        "nicknames": nicknames
    }


def step(player: str, card: Card, next_player: str) -> Dict:
    return {
        "command": "step",
        "player": player,
        "top_card": _card_dict(card),
        "next_player": next_player,
    }


def take_card(player: str, card: Card) -> Dict:
    return {
        "command": "take_card",
        "player": player,
        "card": _card_dict(card),
    }


def end_game(winner: str) -> Dict:
    return {"command": "end_game", "winner": winner}


def dumps(msg: Dict) -> bytes:
    return json.dumps(msg, ensure_ascii=False).encode()


def loads(raw: bytes) -> Dict:
    return json.loads(raw.decode())
