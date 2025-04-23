import json
import socket
import threading

from PyQt5.QtCore import QObject, pyqtSignal, Qt

from core.game_controller import GameController
from core.network_utils import get_local_ip
from logger import logger


class Server(QObject):
    gui_cmd = pyqtSignal(str)

    def __init__(self, value_players=3, nickname=None):
        super().__init__()
        self.gui = None
        self.nickname = nickname
        self.game_started = False
        self.ctrl = GameController(
            value_player=value_players,
            nickname=nickname,
            is_client=False,
            on_send=self._broadcast,
            on_close=self.shutdown
        )

        self.ctrl.state_ready = self.gui_cmd.emit
        self.gui_cmd.connect(self._apply_state, Qt.QueuedConnection)
        self.game_started = False
        self.host = get_local_ip()
        # self.port = get_free_port()
        self.port = 8080
        self.session_code = str(self.port)
        self.value_players = value_players
        self.clients = {}
        self.broadcasting = True

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.value_players)
        logger.info(f"Сервер запущен на {self.host}:{self.port} с кодом сессии: {self.session_code}")

        self.broadcast_thread = threading.Thread(target=self.broadcast_session_code, daemon=True)
        self.broadcast_thread.start()

    def _broadcast(self, data: bytes):
        for sock in self.clients.values():
            try:
                sock.sendall(data)
            except OSError:
                pass

    def broadcast_session_code(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f"{self.session_code}:{self.host}:{self.port}"

        while True:
            if len(self.clients) < self.value_players:
                try:
                    udp_socket.sendto(message.encode(), ("255.255.255.255", self.port))
                    logger.info(f"Отправлен код сессии {self.session_code} по адресу 255.255.255.255:{self.port}")
                except Exception as e:
                    logger.error(f"Ошибка отправки broadcast: {e}")
            threading.Event().wait(5)

    def handle_client(self, client_socket, address):
        logger.info(f"Клиент {address} подключился.")
        try:
            nickname = client_socket.recv(1024).decode("utf-8")
            if nickname == self.nickname or nickname in self.clients:
                client_socket.send("INVALID_NICKNAME".encode("utf-8"))
                client_socket.close()
                return

            self.clients[nickname] = client_socket
            client_socket.send("WELCOME".encode("utf-8"))

            if len(self.clients) == self.value_players:
                logger.info("Достигнуто максимальное количество игроков. Остановка broadcast.")
                self.broadcasting = False

            while True:
                raw = client_socket.recv(8192)
                if not raw:
                    break
                try:
                    data = json.loads(raw.decode("utf-8"))
                    logger.info(f"Команда {data}")
                    self.ctrl.handle_command(data)
                except Exception as e:
                    logger.error(e)
        except:
            pass
        finally:
            self.remove_client(client_socket, nickname)

    def remove_client(self, client_socket, nickname=None):
        if nickname in self.clients:
            del self.clients[nickname]
        client_socket.close()
        logger.info(f"Клиент {nickname} отключился.")

        if not self.game_started:
            if len(self.clients) < self.value_players:
                logger.info("Игрок отключился. Возобновление broadcast.")
                self.broadcasting = True
        else:
            logger.info("Отключение во время игры — аварийное завершение.")
            self.ctrl.handle_error(nickname)

    def start(self):
        logger.info("Для остановки сервера нажмите CTRL+C")
        while True:
            try:
                client_socket, address = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, address), daemon=True).start()
            except OSError:
                break

    def shutdown(self, *_):
        logger.info("Завершаем сервер...")
        try:
            self.server_socket.close()
        except OSError:
            pass

        for sock in list(self.clients.values()):
            try:
                sock.close()
            except OSError:
                pass
        self.clients.clear()

    def _apply_state(self, cmd: str):
        if cmd == "start_game":
            self.game_started = True
        if not self.gui:
            return
        self.gui.apply_state(cmd)
