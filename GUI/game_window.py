import math
import random

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPalette, QBrush, QColor, QTransform, QPen
from PyQt5.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QPushButton

from GUI.draggable_svg_item import DraggableCardItem
from core.card import Card
from core.setting_deploy import get_resource_path
from logger import logger


class GameWindow(QWidget):
    def __init__(self, num_players, is_client=True):
        super().__init__()
        self.num_players = num_players

        self.setWindowTitle("UNO")
        self.setGeometry(100, 100, 1500, 750)
        self.setFixedSize(1500, 750)
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.svg")))

        self.player_hands = {i: [] for i in range(num_players)}

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 1500, 750)

        self.view = QGraphicsView(self.scene, self)
        self.view.setGeometry(0, 0, 1500, 750)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setStyleSheet("background: transparent; border: none;")

        self.arc_config = {
            0: {"cx": 750, "cy": 2100, "r": 1500, "start_angle": 260, "end_angle": 280},
            1: {"cx": 750, "cy": -1350, "r": 1500, "start_angle": 75, "end_angle": 95},
            2: {"cx": 2850, "cy": 400, "r": 1500, "start_angle": -5, "end_angle": 5},
            3: {"cx": -1350, "cy": 400, "r": 1500, "start_angle": -180, "end_angle": -190},
        }

        self.top_card_item = None
        self.deck_items = []

        self.init_ui()
        self.deal_initial_cards()

    def init_ui(self):
        # Фон
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(QColor(173, 216, 230)))
        self.setPalette(palette)

        # Красный прямоугольник для стола
        center_item = QGraphicsRectItem(700, 250, 300, 300)
        center_item.setPen(QPen(Qt.red, 3))
        self.scene.addItem(center_item)

        # Создаем "верхнюю карту" по умолчанию
        self.create_top_card("red", "7")

        # Создаем колоду (5 карт рубашкой)
        for i in range(5):
            deck = DraggableCardItem(get_resource_path("assets/cards/back.svg"), draggable=False)
            deck.setScale(0.5)
            deck.setPos(600 + i * 3, 300 - i * 3)
            self.deck_items.append(deck)
            self.scene.addItem(deck)

        self.add_buttons()

    def add_buttons(self):
        """Кнопки для теста анимаций."""
        self.draw_card_btn = QPushButton("Взять карту", self)
        self.draw_card_btn.setGeometry(50, 650, 120, 40)
        self.draw_card_btn.clicked.connect(lambda: self.animate_draw_card(3, None))

        self.opponent_move_btn = QPushButton("Ход соперника", self)
        self.opponent_move_btn.setGeometry(200, 650, 150, 40)
        self.opponent_move_btn.clicked.connect(lambda: self.animate_opponent_move(1, None))

    def deal_initial_cards(self):
        colors = ["red", "blue", "yellow", "green"]
        values = [str(i) for i in range(10)] + ["draw two", "reverse", "skip"]

        for player in range(self.num_players):
            for _ in range(7):
                if player == 0:
                    c = Card(random.choice(colors), random.choice(values))
                else:
                    c = Card("back", "back")
                self.player_hands[player].append((c, None))
            self.update_player_hand(player)

    def create_top_card(self, color, value):
        """Удаляем старую верхнюю карту, создаём новую."""
        if self.top_card_item:
            self.scene.removeItem(self.top_card_item)

        c = Card(color, value)
        new_top = DraggableCardItem(c.image_path,
                                    draggable=False, card=c)
        new_top.setScale(0.5)
        new_top.setPos(800, 300)
        new_top.setZValue(9999)
        self.scene.addItem(new_top)

        self.top_card_item = new_top
        logger.info(f"Новая верхняя карта: {color} {value}")

    def update_player_hand(self, player_index):
        """Перерисовываем веер."""
        # Удаляем старые item
        for (card, item) in self.player_hands[player_index]:
            if item:
                self.scene.removeItem(item)

        hand_size = len(self.player_hands[player_index])
        if hand_size == 0:
            return

        cfg = self.arc_config[player_index]
        cx, cy, r = cfg["cx"], cfg["cy"], cfg["r"]
        start_angle, end_angle = cfg["start_angle"], cfg["end_angle"]

        if hand_size == 1:
            angle_deg = (start_angle + end_angle) / 2
            self._place_card(player_index, 0, angle_deg, cx, cy, r)
            return

        total_angle = end_angle - start_angle
        step = total_angle / (hand_size - 1) if hand_size > 1 else total_angle

        for i in range(hand_size):
            angle_deg = start_angle + step * i
            self._place_card(player_index, i, angle_deg, cx, cy, r)

    def _place_card(self, player_index, i, angle_deg, cx, cy, r):
        (c, _) = self.player_hands[player_index][i]

        from math import radians
        a = radians(angle_deg)

        if player_index in [0, 1]:
            x = cx + r * math.cos(a)
            y = cy + r * math.sin(a)
        else:
            x = cx - r * math.cos(a)
            y = cy - r * math.sin(a)

        item = DraggableCardItem(c.image_path,
                                 draggable=(player_index == 0 and c.color != "back"), card=c)
        item.setScale(0.5)

        # Повернем карту
        t = QTransform()
        if player_index in [0, 1]:
            t.rotate(angle_deg + 90)
        else:
            t.rotate(angle_deg - 90)
        item.setTransform(t)

        # Логика хода для нижнего игрока
        if player_index == 0 and c.color != "back":
            def dropped():
                self.remove_card_from_player(0, c)
                self.create_top_card(c.color, c.value)
                self.update_player_hand(0)

            item.card_dropped_in_center = dropped

            def compare_cards(card_obj):
                return self.top_card_item.card.can_play_on(card_obj)

            item.compare_cards = compare_cards

        self.scene.addItem(item)
        item.setPos(x, y)

        self.player_hands[player_index][i] = (c, item)

    def remove_card_from_player(self, player_index, card_to_remove):
        new_hand = []
        for (c, item) in self.player_hands[player_index]:
            if c == card_to_remove:
                if item:
                    self.scene.removeItem(item)
            else:
                new_hand.append((c, item))
        self.player_hands[player_index] = new_hand
        self.update_player_hand(player_index)

    def animate_draw_card(self, player_index, card):
        """
        Анимация: карта из колоды -> рука player_index
        Если card=None, генерим новую (если player=0, открытая).
        """
        if not self.deck_items:
            return

        deck_item = self.deck_items.pop()
        deck_item.setZValue(500)

        if card is None:
            # Генерим
            if player_index == 0:
                colors = ["red", "blue", "yellow", "green"]
                values = [str(i) for i in range(10)] + ["draw two", "reverse", "skip"]
                card = Card(random.choice(colors), random.choice(values))
            else:
                card = Card("back", "back")

        def on_finish():
            self.scene.removeItem(deck_item)
            # Добавляем карту в руку
            self.player_hands[player_index].append((card, None))
            self.update_player_hand(player_index)

        cfg = self.arc_config[player_index]
        if player_index in [2, 3]:
            t = QTransform()
            t.rotate(90)
            deck_item.setTransform(t)
            deck_item.setPos(850, 350)
            if player_index == 3:
                deck_item.setPos(720, 350)
        deck_item.fly_to_position(cfg["cx"], cfg["cy"], 3000, callback=on_finish)

    def animate_opponent_move(self, player_index, card):
        if len(self.player_hands[player_index]) == 0 and not card:
            return

        if card is None:
            (c, item) = self.player_hands[player_index][0]
            self.player_hands[player_index].pop(0)
        else:
            c = card
            item = None

        if c.color == "back":
            colors = ["red", "blue", "yellow", "green"]
            values = [str(i) for i in range(10)] + ["draw two", "reverse", "skip"]
            c = Card(random.choice(colors), random.choice(values))

        if not item:
            item = DraggableCardItem(c.image_path, draggable=False, card=c)
            item.setScale(0.5)
            self.scene.addItem(item)

        item.setZValue(800)
        t = QTransform()
        t.reset()
        item.setTransform(t)

        def on_finish():
            self.scene.removeItem(item)
            self.create_top_card(c.color, c.value)
            self.update_player_hand(player_index)

        item.fly_to_position(800, 300, 500, callback=on_finish)
