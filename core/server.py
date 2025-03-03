import socket
import threading

from logger import logger


def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Server:
    def __init__(self, max_clients=3, nickname=None):
        self.nickname = nickname
        self.host = get_local_ip()
        self.port = get_free_port()
        self.session_code = str(self.port)
        self.max_clients = max_clients
        self.clients = {}
        self.broadcasting = True  # Флаг для контроля отправки broadcast

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_clients)
        logger.info(f"Сервер запущен на {self.host}:{self.port} с кодом сессии: {self.session_code}")

        self.broadcast_thread = threading.Thread(target=self.broadcast_session_code, daemon=True)
        self.broadcast_thread.start()

    def broadcast_session_code(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f"{self.session_code}:{self.host}:{self.port}"

        while True:
            if len(self.clients) < self.max_clients:  # Отправлять, если не заполнено
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

            if len(self.clients) == self.max_clients:
                logger.info("Достигнуто максимальное количество игроков. Остановка broadcast.")
                self.broadcasting = False

            while True:
                message = client_socket.recv(1024).decode("utf-8")
                if not message:
                    break
                logger.info(f"{nickname} сказал: {message}")
                self.broadcast(f"{nickname}: {message}", client_socket)
        except:
            pass
        finally:
            self.remove_client(client_socket, nickname)

    def remove_client(self, client_socket, nickname=None):
        if nickname in self.clients:
            del self.clients[nickname]
        client_socket.close()
        logger.info(f"Клиент {nickname} отключился.")

        if len(self.clients) < self.max_clients:  # Если кто-то вышел, снова включаем broadcast
            logger.info("Игрок отключился. Возобновление broadcast.")
            self.broadcasting = True

    def start(self):
        logger.info("Для остановки сервера нажмите CTRL+C")
        while True:
            try:
                client_socket, address = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, address), daemon=True).start()
            except OSError:
                break
