import socket
import threading
import time
from logger import logger


def find_server_by_port(port):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    try:
        udp_socket.bind(("", port))  # Слушаем конкретный порт, который совпадает с кодом сессии
    except OSError as e:
        logger.error(f"Ошибка при привязке к порту {port}: {e}")
        return None, None

    logger.info(f"Поиск сервера на порте {port}...")
    timeout = time.time() + 15  # Ждем 15 секунд

    while time.time() < timeout:
        try:
            udp_socket.settimeout(5)
            data, addr = udp_socket.recvfrom(1024)
            received_code, ip, server_port = data.decode().split(":")
            if received_code == str(port):  # Сравниваем с введенным портом
                logger.info(f"Найден сервер {ip}:{server_port}")
                return ip, int(server_port)
        except socket.timeout:
            logger.info("Не получено данных, повторяем попытку...")

    logger.error("Ошибка: Сервер не найден.")
    return None, None


class Client:
    def __init__(self, session_code, nickname, join_window):
        self.join_window = join_window
        self.server_ip, self.server_port = find_server_by_port(int(session_code))  # Код сессии - это порт
        if self.server_ip is None:
            self.join_window.show_error("Ошибка: сервер не найден!")
            return

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            self.join_window.show_status("Подключение установлено...")
        except:
            self.join_window.show_error("Ошибка подключения к серверу!")
            return

        # Отправляем никнейм серверу
        self.send_message(nickname)

        # Получаем ответ от сервера (валидный никнейм или нет)
        response = self.client_socket.recv(1024).decode("utf-8")

        if response == "INVALID_NICKNAME":
            self.join_window.show_error("Ошибка: Никнейм уже занят! Выберите другой.")
            self.close()
            return

        self.join_window.show_success("Вы успешно подключились! Ожидайте начала игры.")
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def send_message(self, message):
        self.client_socket.send(message.encode("utf-8"))

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode("utf-8")
                self.join_window.show_status(message)
            except:
                self.join_window.show_error("Отключение от сервера")
                self.close()
                break

    def close(self):
        self.client_socket.close()
