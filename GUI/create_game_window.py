import threading

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QListWidget

from GUI.game_window import GameWindow
from GUI.stat_pos import get_nicknames
from core.server import Server
from core.setting_deploy import get_resource_path


class CreateGameWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.server = None
        self.main_window = parent
        self.setWindowTitle("UNO")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.svg")))
        self.setGeometry(300, 200, 400, 400)
        self.setStyleSheet("background-color: #ffcc00; border-radius: 10px;")
        self.setModal(True)

        layout = QVBoxLayout()

        label_nickname = QLabel("Выберите никнейм:")
        label_nickname.setStyleSheet("font-size: 18px; color: #333; font-weight: bold;")
        layout.addWidget(label_nickname)

        self.nickname_combo = QComboBox()
        self.nickname_combo.addItem("-- Выберите никнейм --")
        self.nickname_combo.addItems(get_nicknames())
        self.nickname_combo.currentIndexChanged.connect(self.show_players_choice)
        self.nickname_combo.setStyleSheet("background-color: white; padding: 5px; font-size: 16px;")
        layout.addWidget(self.nickname_combo)

        self.label_players = QLabel("Выберите количество игроков (2-4):")
        self.label_players.setStyleSheet("font-size: 18px; color: #333; font-weight: bold;")
        self.label_players.setVisible(False)
        layout.addWidget(self.label_players)

        self.players_combo = QComboBox()
        self.players_combo.addItem("-- Выберите кол-во игроков --")
        self.players_combo.addItems(["2", "3", "4"])
        self.players_combo.currentIndexChanged.connect(self.show_generate_button)
        self.players_combo.setVisible(False)
        self.players_combo.setStyleSheet("background-color: white; padding: 5px; font-size: 16px;")
        layout.addWidget(self.players_combo)

        self.generate_button = QPushButton("Сгенерировать Код Доступа")
        self.generate_button.clicked.connect(self.start_server)
        self.generate_button.setVisible(False)
        self.generate_button.setStyleSheet(
            "background-color: #ff5733; color: white; font-size: 18px; font-weight: bold; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.generate_button)

        self.code_label = QLabel("Код Доступа: ")
        self.code_label.setStyleSheet("font-size: 20px; color: #333; font-weight: bold;")
        self.code_label.setVisible(False)
        layout.addWidget(self.code_label)

        self.players_list = QListWidget()
        self.players_list.setStyleSheet("background-color: white; font-size: 16px; padding: 5px;")
        self.players_list.setVisible(False)
        layout.addWidget(self.players_list)

        self.start_game_button = QPushButton("Начать игру")
        self.start_game_button.setStyleSheet(
            "background-color: #28a745; color: white; font-size: 18px; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.start_game_button.setVisible(False)
        self.start_game_button.clicked.connect(self.on_start_game)
        layout.addWidget(self.start_game_button)

        self.setLayout(layout)

    def show_players_choice(self):
        if self.nickname_combo.currentIndex() > 0:
            self.label_players.setVisible(True)
            self.players_combo.setVisible(True)
            self.nickname_combo.setDisabled(True)

    def show_generate_button(self):
        if self.players_combo.currentIndex() >= 0:
            self.generate_button.setVisible(True)
            self.players_combo.setDisabled(True)

    def start_server(self):
        self.server = Server(value_players=int(self.players_combo.currentText()) - 1,
                             nickname=self.nickname_combo.currentText())
        self.code_label.setText(f"Код доступа: {self.server.session_code}")
        self.code_label.setVisible(True)
        self.players_list.setVisible(True)
        self.generate_button.setVisible(False)

        threading.Thread(target=self.server.start, daemon=True).start()
        threading.Thread(target=self.update_players_list, daemon=True).start()

    def update_players_list(self):
        while True:
            self.players_list.clear()
            for nickname in self.server.clients.keys():
                self.players_list.addItem(nickname)
            if len(self.server.clients) == self.server.value_players:
                self.start_game_button.setVisible(True)

            else:
                self.start_game_button.setVisible(False)
            threading.Event().wait(2)

    def closeEvent(self, event):
        if self.server:
            self.server.shutdown(None, None)

    def on_start_game(self):
        self.server.gui = GameWindow(num_players=self.server.value_players + 1, main_window=self.main_window)
        self.server.gui.show()
        self.server.gui.ctrl = self.server.ctrl
        self.server.ctrl.new_game([self.server.nickname, *self.server.clients])
        self.accept()
