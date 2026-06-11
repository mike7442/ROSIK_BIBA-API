# tcp_server.py
import socket
import threading
import time
import struct # Для упаковки/распаковки байтов, если нужно будет

SERVER_IP = '192.168.0.221'  # Принимать подключения на любом интерфейсе
SERVER_PORT = 31415
PACKET_SIZE_CLIENT_TO_SERVER = 10
PACKET_SIZE_SERVER_TO_CLIENT = 50
START_HEADER = b'\xAA\xBB' # Произвольный заголовок
HEARTBEAT_TIMEOUT_S = 0.50
SEND_INTERVAL_MS = 50
RECV_TIMEOUT_S = 0.04 # Для неблокирующего получения пакета от клиента в основном цикле

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

def server_main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(1) # Ожидаем максимум 1 соединение
    print(f"Сервер слушает на {SERVER_IP}:{SERVER_PORT}")

    client_socket = None
    last_received_packet_time = 0
    is_client_active = False
    heartbeat_timeout = HEARTBEAT_TIMEOUT_S

    def send_packets_loop():
        nonlocal client_socket, is_client_active
        while True:
            if is_client_active and client_socket:
                try:
                    # Создаем 50-байтный пакет (например, с заголовком и мусором)
                    payload_data = b'\x00' * (PACKET_SIZE_SERVER_TO_CLIENT - len(START_HEADER))
                    packet = START_HEADER + payload_data
                    client_socket.sendall(packet)
                    print(f"[DEBUG] Сервер отправил 50 байт.")
                except (BrokenPipeError, ConnectionResetError, OSError) as e:
                    print(f"[ERROR] Ошибка отправки пакета клиенту: {e}")
                    is_client_active = False
                    client_socket.close()
                    client_socket = None
                    break
            elif not is_client_active:
                 # Если клиент неактивен, ждем новое подключение
                 # Основной цикл handle_client будет ждать accept
                 time.sleep(0.1) # Небольшая задержка, чтобы не грузить CPU
                 continue

            time.sleep(SEND_INTERVAL_MS / 1000.0)

    def handle_client_loop():
        nonlocal client_socket, last_received_packet_time, is_client_active, server_socket
        send_thread = None

        while True:
            if not is_client_active:
                print("Сервер ожидает подключение клиента...")
                try:
                    client_socket, addr = server_socket.accept()
                    print(f"Подключен клиент: {addr}")
                    client_socket.settimeout(RECV_TIMEOUT_S) # Устанавливаем таймаут на recv
                    last_received_packet_time = time.time()
                    is_client_active = True
                    # Запускаем поток отправки пакетов только после подключения
                    if send_thread is None or not send_thread.is_alive():
                         send_thread = threading.Thread(target=send_packets_loop, daemon=True)
                         send_thread.start()
                except socket.timeout:
                     # accept не использует timeout, но на всякий случай
                     continue
                except Exception as e:
                     print(f"[ERROR] Ошибка при подключении клиента: {e}")
                     continue
            else:
                # Клиент активен, проверяем таймаут
                current_time = time.time()
                if current_time - last_received_packet_time > heartbeat_timeout:
                    print("[INFO] Таймаут клиента! Отключаю соединение.")
                    is_client_active = False
                    if client_socket:
                        client_socket.close()
                        client_socket = None
                    # Цикл вернётся к ожиданию accept
                    continue

                # Пытаемся получить пакет от клиента
                try:
                    packet = find_header(client_socket, PACKET_SIZE_CLIENT_TO_SERVER, START_HEADER)
                    if packet:
                        print(f"[DEBUG] Сервер получил 10 байт: {packet[:10]}")
                        last_received_packet_time = time.time() # Обновляем время получения
                    else:
                        # find_header вернул None -> соединение закрыто
                        print("[INFO] Клиент отключился (соединение закрыто).")
                        is_client_active = False
                        client_socket.close()
                        client_socket = None
                        # Цикл вернётся к ожиданию accept
                        continue
                except socket.timeout:
                    # recv вернул timeout - это нормально, просто не получили пакет вовремя
                    pass # Не обновляем last_received_packet_time
                except (ConnectionResetError, BrokenPipeError, OSError) as e:
                    print(f"[ERROR] Ошибка получения от клиента: {e}")
                    is_client_active = False
                    if client_socket:
                        client_socket.close()
                        client_socket = None
                    # Цикл вернётся к ожиданию accept
                    continue

                time.sleep(0.01) # Небольшая задержка, чтобы не грузить CPU в цикле ожидания пакета

    try:
        handle_client_loop()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        if client_socket:
            client_socket.close()
        server_socket.close()

if __name__ == "__main__":
    server_main()
