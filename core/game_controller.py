import json

from core.deck import Deck
from logger import logger


class GameController:
    def __init__(self, is_server, server=None, client_socket=None):
        """
        :param is_server: True/False
        :param server: объект Server (если is_server=True)
        :param client_socket: сокет клиента (если is_server=False)
        """
        self.is_server = is_server
        self.server = server
        self.client_socket = client_socket

        self.deck = Deck()
        self.top_card = None
        self.hands = {}  # {nickname: [Card, Card, ...]}
        self.turn_order = []  # список никнеймов в порядке ходов
        self.current_player_index = 0

    def start_game(self, nicknames):
        """
        Запускаем игру: генерируем колоду, раздаём карты, выбираем верхнюю карту стола.
        """
        self.deck.shuffle()
        # Для 2..4 игроков
        num_players = len(nicknames)

        # Раздаём
        deals = self.deck.deal_cards(num_players)
        for i, nickname in enumerate(nicknames):
            self.hands[nickname] = deals[i]

        # Тянем первую карту на стол
        while True:
            c = self.deck.draw_card()
            # Если первая карта - НЕ спецкарта? Или разрешаем любую
            if c:
                self.top_card = c
                break

        self.turn_order = nicknames[:]
        logger.info(f"Старт игры. Верхняя карта: {self.top_card}")

        # Отправляем каждому игроку его карты, а также общую top_card
        self.broadcast_state()

    def broadcast_state(self):
        """
        Отправляет всем текущее состояние игры:
         - top_card
         - игроку – его карты
         - кто ходит сейчас
        """
        if not self.is_server:
            return  # Только сервер рассылает

        import json
        for nickname, sock in self.server.clients.items():
            # Формируем сообщение
            data = {
                "type": "game_state",
                "top_card": {"color": self.top_card.color, "value": self.top_card.value},
                "your_cards": [c.__dict__ for c in self.hands[nickname]],
                "current_player": self.turn_order[self.current_player_index]
            }
            msg = json.dumps(data)
            sock.send(msg.encode("utf-8"))

    def handle_play_card(self, nickname, card_info):
        """
        Сервер: игрок nickname сыграл карту card_info.
        Убираем из руки, делаем её top_card, рассылаем state
        """
        # Находим Card в self.hands[nickname], убираем
        from core.card import Card
        played_card = Card(card_info["color"], card_info["value"], card_info["action"])
        if played_card in self.hands[nickname]:
            self.hands[nickname].remove(played_card)
            self.top_card = played_card

            # Следующий ход
            self.current_player_index = (self.current_player_index + 1) % len(self.turn_order)

            self.broadcast_state()

    def handle_draw_card(self, nickname):
        """
        Игрок взял карту из колоды
        """
        c = self.deck.draw_card()
        self.hands[nickname].append(c)
        self.broadcast_state()

    def process_message(self, sock, msg):
        """
        Сервер обрабатывает входящие сообщения JSON.
        """
        data = json.loads(msg)
        if data["type"] == "play_card":
            self.handle_play_card(data["nickname"], data["card"])
        elif data["type"] == "draw_card":
            self.handle_draw_card(data["nickname"])
        # ... прочие типы

    # На клиенте тоже можно хранить аналогичный GameController,
    # где process_message() обновляет локальный GameWindow
