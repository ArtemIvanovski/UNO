from __future__ import annotations

import math
import random

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPalette, QBrush, QColor, QTransform
from PyQt5.QtSvg import QGraphicsSvgItem
from PyQt5.QtWidgets import QGraphicsEllipseItem
from PyQt5.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsSceneMouseEvent, \
    QMessageBox, QGraphicsTextItem

from GUI.draggable_svg_item import DraggableCardItem
from GUI.stat_pos import get_name_positions, get_arc_config, get_color_map
from core.card import Card
from core.game_controller import GameController
from core.setting_deploy import get_resource_path
from logger import logger


class GameWindow(QWidget):
    def __init__(self, num_players, ctrl: GameController = None, main_window=None):
        super().__init__()
        self._pending_card: Card | None = None
        self.color_map = get_color_map()
        self.click_blocker = None
        self.ctrl = ctrl
        self.main_window = main_window
        self.main_window.hide()
        self.turn_order = []
        self.take_card_button = None
        self.draw_card_btn = None
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
        self.name_items = {}

        self.name_positions = get_name_positions()

        self.arc_config = get_arc_config()
        self.top_card_item = None
        self.deck_items = []
        self.create_click_blocker()
        self.init_ui()

    def init_ui(self):
        palette = QPalette()
        palette.setBrush(QPalette.Background, QBrush(QColor(173, 216, 230)))
        self.setPalette(palette)

        for i in range(108 - self.num_players * 7 - 1):
            deck = DraggableCardItem(get_resource_path("assets/cards/back.svg"), draggable=False)
            deck.setScale(0.5)
            deck.setPos(600 + i * 0.1, 300 - i * 0.1)
            self.deck_items.append(deck)
            self.scene.addItem(deck)

        self.add_buttons()
        self._init_color_indicator()
        self._init_color_picker()

    def _init_color_indicator(self):
        r = 15
        x, y = 950, 280
        self.color_indicator = QGraphicsEllipseItem(x, y, r * 2, r * 2)
        self.color_indicator.setBrush(QBrush(Qt.transparent))
        self.color_indicator.setZValue(10001)
        self.scene.addItem(self.color_indicator)

    def set_color_indicator(self, color_name: str | None):
        if color_name and color_name in self.color_map:
            hexcol = self.color_map[color_name]
            self.color_indicator.setBrush(QBrush(QColor(hexcol)))
            self.color_indicator.setVisible(True)
        else:
            self.color_indicator.setVisible(False)

    def _init_color_picker(self):
        self.color_picker = []
        r = 25
        base_x, base_y = 790, 550
        gap = 70
        for i, (name, hexcol) in enumerate(self.color_map.items()):
            circle = QGraphicsEllipseItem(
                base_x + (i - (len(self.color_map) - 1) / 2) * gap - r,
                base_y - r,
                r * 2, r * 2
            )
            circle.setBrush(QBrush(QColor(hexcol)))
            circle.setZValue(10002)
            circle.setVisible(False)
            circle._color_name = name
            circle.mousePressEvent = lambda evt, item=circle: self._on_color_chosen(item._color_name)
            self.scene.addItem(circle)
            self.color_picker.append(circle)

    def show_color_picker(self):
        for c in self.color_picker:
            c.setVisible(True)

    def hide_color_picker(self):
        for c in self.color_picker:
            c.setVisible(False)

    def add_buttons(self):
        self.draw_card_btn = QGraphicsSvgItem(get_resource_path("assets/iconTakeCard.svg"))
        self.draw_card_btn.setScale(0.4)
        self.draw_card_btn.setPos(250, 500)
        self.scene.addItem(self.draw_card_btn)
        self.take_card_button = True
        self.draw_card_btn.mousePressEvent = self.on_draw_card_click
        self.update_button_state()

    def on_draw_card_click(self, event: QGraphicsSceneMouseEvent):
        self.draw_card_btn.setOpacity(0.6)
        take_card = self.ctrl.draw_one()
        self.take_card(0, take_card)
        self.draw_card_btn.setOpacity(1.0)
        self.update_button_state()

    def update_button_state(self):
        if self.take_card_button:
            self.draw_card_btn.setAcceptedMouseButtons(Qt.LeftButton)
            self.draw_card_btn.setOpacity(1.0)
        else:
            self.draw_card_btn.setAcceptedMouseButtons(Qt.NoButton)
            self.draw_card_btn.setOpacity(0.3)

    def create_top_card(self, card: Card):
        if self.top_card_item:
            self.scene.removeItem(self.top_card_item)
        if card.action not in ["draw four", "wild"]:
            self.set_color_indicator(None)
        else:
            self.set_color_indicator(card.color)

        new_top = DraggableCardItem(card.image_path,
                                    draggable=False, card=card)
        new_top.setScale(0.5)
        new_top.setPos(800, 300)
        new_top.setZValue(9999)
        self.scene.addItem(new_top)

        self.top_card_item = new_top
        logger.info(f"Новая верхняя карта: {card}")

    def update_player_hand(self, player_index):
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

        can_drag = (
                player_index == 0 and
                c.color != "back" and
                self.ctrl.is_my_step
        )

        item = DraggableCardItem(c.image_path,
                                 draggable=can_drag, card=c)
        item.setScale(0.5)

        t = QTransform()
        if player_index in [0, 1]:
            t.rotate(angle_deg + 90)
        else:
            t.rotate(angle_deg - 90)
        item.setTransform(t)

        if player_index == 0 and c.color != "back":
            def dropped():
                self.remove_card_from_player(0, c)
                self.create_top_card(c)
                self.update_player_hand(0)

                if c.action in ("draw four", "wild"):
                    self._pending_card = c
                    self.show_color_picker()
                else:
                    self.ctrl.play_card(card=c)
                    self.update()

            item.card_dropped_in_center = dropped

            def compare_cards(card_obj):
                logger.info(f"compare_cards {self.top_card_item.card.can_play_on(card_obj)}")
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

    def take_card(self, player_index, card):
        if not self.deck_items:
            return

        deck_item = self.deck_items.pop()
        deck_item.setZValue(500)

        if card is None and player_index != 0:
            card = Card("back", "back")

        def on_finish():
            self.scene.removeItem(deck_item)
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
        deck_item.fly_to_position(cfg["cx"], cfg["cy"], 1000, callback=on_finish)

    def animate_opponent_move(self, player_index, card):
        if len(self.player_hands[player_index]) == 0 and not card:
            return

        if self.player_hands[player_index]:
            self.player_hands[player_index].pop(0)

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
            self.create_top_card(c)
            self.update_player_hand(player_index)

        item.fly_to_position(800, 300, 500, callback=on_finish)

    def apply_state(self, command: str):
        logger.info(f"Обработка команды {command}")
        if command == "start_game":
            self.create_top_card(self.ctrl.top_card)

            self.player_hands = {i: [] for i in range(self.num_players)}

            for idx in range(self.num_players):
                if idx == 0:
                    cards = list(self.ctrl.my_hands)
                else:
                    cards = [Card("back", "back") for _ in range(7)]

                self.player_hands[idx] = [(c, None) for c in cards]
                self.update_player_hand(idx)

        elif command == "step" or command == "wild":
            self.animate_opponent_move(self.swap_queue().index(self.ctrl.step_player), self.ctrl.top_card)
            self.create_top_card(self.ctrl.top_card)
        elif command == "take_card":
            self.take_card(self.swap_queue().index(self.ctrl.player_take_card), None)
        elif command == "draw two":
            self.animate_opponent_move(self.swap_queue().index(self.ctrl.step_player), self.ctrl.top_card)
            self.create_top_card(self.ctrl.top_card)
            self._draw_cards(count=2)
        elif command == "draw four":
            self.animate_opponent_move(self.swap_queue().index(self.ctrl.step_player), self.ctrl.top_card)
            self.create_top_card(self.ctrl.top_card)
            self._draw_cards(count=4)
        elif command == "end_game":
            msgbox = QMessageBox(self)
            msgbox.setWindowTitle("Игра окончена")
            msgbox.setText(f"Победил игрок: {self.ctrl.winner_player}")
            msgbox.setIcon(QMessageBox.Information)
            msgbox.setStandardButtons(QMessageBox.Ok)

            ret = msgbox.exec_()

            if ret == QMessageBox.Ok:
                if self.main_window is not None:
                    self.main_window.show()
                self.ctrl.close_game()
                self.close()
        elif command == "error":
            if self.ctrl.is_client:
                text = "Соединение с сервером потеряно."
            else:
                text = f"Игрок {self.ctrl.exit_nickname} отключился — игра прервана."
            QMessageBox.critical(self, "Ошибка", text)
            if self.main_window:
                self.main_window.show()
            self.ctrl.close_game()
            self.close()
        self.update()

    def swap_queue(self):
        full_queue = self.ctrl.queue[:]
        if self.ctrl.my_nickname in full_queue:
            start = full_queue.index(self.ctrl.my_nickname)
            display_queue = full_queue[start:] + full_queue[:start]
        else:
            display_queue = full_queue
        return display_queue

    def update(self):
        for idx, items in self.name_items.items():
            self.scene.removeItem(items)
        self.name_items.clear()

        display_queue = self.swap_queue()
        self.ctrl.is_my_step = self.ctrl.current == self.ctrl.my_nickname
        self.click_blocker.setVisible(not self.ctrl.is_my_step)
        logger.info(f"Кто ходит {self.ctrl.current}")
        logger.info(f"колво карт в деке {len(self.ctrl.deck)}")
        for i in range(self.ctrl.value_player):
            self.update_player_hand(i)
        self.take_card_button = self.ctrl.is_my_step
        self.update_button_state()

        for idx, nick in enumerate(display_queue):
            if idx >= self.num_players:
                break
            x, y, angle = self.name_positions[idx]
            text = QGraphicsTextItem(nick)
            text.setPos(x, y)
            text.setRotation(angle)
            if nick == self.ctrl.current:
                text.setDefaultTextColor(Qt.red)
            else:
                text.setDefaultTextColor(Qt.black)
            self.scene.addItem(text)
            self.name_items[idx] = text

    def create_click_blocker(self):
        self.click_blocker = QGraphicsRectItem(self.scene.sceneRect())
        self.click_blocker.setBrush(QBrush(QColor(0, 0, 0, 0)))
        self.click_blocker.setZValue(10000)
        self.click_blocker.setAcceptHoverEvents(True)
        self.click_blocker.setAcceptedMouseButtons(Qt.AllButtons)
        self.click_blocker.mousePressEvent = lambda event: None
        self.click_blocker.mouseReleaseEvent = lambda event: None
        self.click_blocker.mouseMoveEvent = lambda event: None
        self.click_blocker.setVisible(False)
        self.scene.addItem(self.click_blocker)

    def _draw_cards(self, count: int = 1):
        def _draw_one(i):
            if i >= count:
                return
            card = self.ctrl.draw_one()
            self.take_card(0, card)
            QTimer.singleShot(300, lambda: _draw_one(i + 1))

        _draw_one(0)

    def _on_color_chosen(self, color_name: str):
        if not self._pending_card:
            return
        self._pending_card.color = color_name
        self.set_color_indicator(color_name)
        self.create_top_card(self._pending_card)
        self.hide_color_picker()
        self.ctrl.play_card(card=self._pending_card)
        self._pending_card = None
        self.update()
