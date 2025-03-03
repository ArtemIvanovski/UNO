from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QLineEdit

from core.client import Client
from core.setting_deploy import get_resource_path, get_nicknames


class JoinGameWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UNO")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.svg")))
        self.setGeometry(300, 200, 400, 400)
        self.setStyleSheet("background-color: #ffcc00; border-radius: 10px;")
        self.setModal(True)

        self.client = None

        layout = QVBoxLayout()

        label_nickname = QLabel("Выберите никнейм:")
        label_nickname.setStyleSheet("font-size: 18px; color: #333; font-weight: bold;")
        layout.addWidget(label_nickname)

        self.nickname_combo = QComboBox()
        self.nickname_combo.addItem("-- Выберите никнейм --")
        self.nickname_combo.addItems(get_nicknames())
        self.nickname_combo.currentIndexChanged.connect(self.show_code_input)
        self.nickname_combo.setStyleSheet("background-color: white; padding: 5px; font-size: 16px;")

        layout.addWidget(self.nickname_combo)

        self.label_code = QLabel("Введите код доступа:")
        self.label_code.setStyleSheet("font-size: 18px; color: #333; font-weight: bold;")
        self.label_code.setVisible(False)
        layout.addWidget(self.label_code)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Введите код...")
        self.code_input.setStyleSheet("background-color: white; padding: 5px; font-size: 16px;")
        self.code_input.setVisible(False)
        layout.addWidget(self.code_input)

        self.join_button = QPushButton("Присоединиться к игре")
        self.join_button.setVisible(False)
        self.join_button.clicked.connect(self.join_game)
        self.join_button.setStyleSheet(
            "background-color: #ff5733; color: white; font-size: 18px; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.join_button.setDisabled(True)
        layout.addWidget(self.join_button)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 18px; color: green; font-weight: bold;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def show_code_input(self):
        if self.nickname_combo.currentIndex() > 0:
            self.label_code.setVisible(True)
            self.code_input.setVisible(True)
            self.join_button.setVisible(True)
            self.join_button.setDisabled(False)
            self.nickname_combo.setDisabled(True)

    def join_game(self):
        session_code = self.code_input.text().strip()
        if not session_code:
            self.show_error("Введите код!")
            return

        self.show_status("Подключение...")

        nickname = self.nickname_combo.currentText()
        self.client = Client(session_code, nickname, self)

    def show_error(self, message):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("font-size: 18px; color: red; font-weight: bold;")
        self.status_label.setVisible(True)
        self.join_button.setVisible(False)
        self.nickname_combo.setCurrentIndex(0)
        self.nickname_combo.setDisabled(False)

    def show_success(self, message="Вы успешно подключились! Ожидайте начала игры."):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("font-size: 18px; color: green; font-weight: bold;")
        self.status_label.setVisible(True)

    def show_status(self, message):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("font-size: 18px; color: blue; font-weight: bold;")
        self.status_label.setVisible(True)
