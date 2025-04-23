import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QSplitter, QTextBrowser

from core.setting_deploy import get_resource_path
from logger import logger


class RulesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UNO")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.svg")))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        self.text_browser = QTextBrowser()
        splitter.addWidget(self.text_browser)

        self.load_initial_content()

    def load_initial_content(self):
        self.load_html("rules.html")

    def load_html(self, file_name):
        base_dir = os.path.dirname('assets')
        file_path = os.path.join('assets', file_name)
        try:
            with open(get_resource_path(file_path), 'r', encoding='utf-8') as file:
                html_content = file.read()

                self.text_browser.setSearchPaths([base_dir])
                self.text_browser.setHtml(html_content)

        except FileNotFoundError:
            self.text_browser.setHtml("<h1>404</h1><p>Страница не найдена</p>")
            logger.error("Страница не найдена: " + file_name)