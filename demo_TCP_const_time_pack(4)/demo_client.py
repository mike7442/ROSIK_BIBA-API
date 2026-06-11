# tcp_client.py
import socket
import time
import struct # Для упаковки/распаковки байтов, если нужно будет

SERVER_IP = '192.168.0.221' # Замените на IP вашего сервера
SERVER_PORT = 31415
PACKET_SIZE_CLIENT_TO_SERVER = 10
PACKET_SIZE_SERVER_TO_CLIENT = 50
START_HEADER = b'\xAA\xBB'
HEARTBEAT_TIMEOUT_S = 0.5 # Максимальное время между получением пакетов от сервера
SEND_INTERVAL_MS = 50
RECV_TIMEOUT_S = 0.04 # Для recv с таймаутом

def find_header(sock, packet_size, header):
    """Поиск заголовка и чтение оставшихся байт."""
    buffer = b""
    header_len = len(header)

    while True:
        chunk = sock.recv(header_len - len(buffer))
        if not chunk:
            return None # Соединение закрыто
        buffer += chunk
        if len(buffer) >= header_len:
            if buffer[:header_len] == header:
                remaining_bytes_needed = packet_size - header_len
                if remaining_bytes_needed > 0:
                    remaining_chunk = sock.recv(remaining_bytes_needed)
                    if len(remaining_chunk) < remaining_bytes_needed:
                        return None # Неполный пакет или соединение закрыто
                    full_packet = buffer + remaining_chunk
                else:
                    full_packet = buffer
                return full_packet
            else:
                # Сдвигаем буфер на 1 байт, если заголовок не найден
                buffer = buffer[1:]

def client_main():
    client_socket = None
    last_received_packet_time = 0
    is_connected = False
    is_safe_to_move = False
    safety_timeout = HEARTBEAT_TIMEOUT_S

    while True:
        # Проверяем соединение
        if not is_connected:
            print("Клиент пытается подключиться...")
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((SERVER_IP, SERVER_PORT))
                client_socket.settimeout(RECV_TIMEOUT_S) # Устанавливаем таймаут на recv
                print("Клиент подключен к серверу.")
                is_connected = True
                # При успешном подключении сбрасываем время получения
                last_received_packet_time = time.time()
            except Exception as e:
                print(f"[ERROR] Не удалось подключиться: {e}. Ждём 3 секунды перед повторной попыткой...")
                time.sleep(3) # Ждем 3 секунды перед новой попыткой
                continue # Переходим к следующей итерации цикла

        if is_connected:
            # Пытаемся получить 50-байтный пакет от сервера
            try:
                packet = find_header(client_socket, PACKET_SIZE_SERVER_TO_CLIENT, START_HEADER)
                if packet:
                    print(f"[DEBUG] Клиент получил 50 байт: {len(packet)} bytes")
                    last_received_packet_time = time.time() # Обновляем время получения
                else:
                    # find_header вернул None -> соединение закрыто
                    print("[INFO] Соединение с сервером потеряно (сервер закрыл соединение).")
                    is_connected = False
                    is_safe_to_move = False # Сразу ставим в False при потере связи
                    client_socket.close()
                    client_socket = None
                    continue # Переходим к попытке переподключения
            except socket.timeout:
                # recv вернул timeout - это нормально, просто не получили пакет вовремя
                pass # Не обновляем last_received_packet_time
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                print(f"[ERROR] Ошибка получения от сервера: {e}")
                is_connected = False
                is_safe_to_move = False
                client_socket.close()
                client_socket = None
                continue # Переходим к попытке переподключения

            # Обновляем переменную is_safe_to_move
            current_time = time.time()
            if current_time - last_received_packet_time <= safety_timeout:
                if not is_safe_to_move:
                    print("[SAFE] Движение разрешено.")
                is_safe_to_move = True
            else:
                if is_safe_to_move:
                    print("[UNSAFE] Движение запрещено - связь потеряна.")
                is_safe_to_move = False

            # Отправляем 10-байтный пакет
            try:
                payload_data = b'\xCC' * (PACKET_SIZE_CLIENT_TO_SERVER - len(START_HEADER)) # Произвольные данные
                packet_to_send = START_HEADER + payload_data
                client_socket.sendall(packet_to_send)
                print(f"[DEBUG] Клиент отправил 10 байт.")
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                print(f"[ERROR] Ошибка отправки пакета серверу: {e}")
                is_connected = False
                is_safe_to_move = False
                client_socket.close()
                client_socket = None
                continue # Переходим к попытке переподключения

            time.sleep(SEND_INTERVAL_MS / 1000.0) # Ждем 500 мс перед следующей итерацией

if __name__ == "__main__":
    client_main()