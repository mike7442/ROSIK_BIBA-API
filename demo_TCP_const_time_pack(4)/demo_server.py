import socket
import time
# Импортируем наши функции и конфигурацию
from demo_protocol_utils import pack_message, MESSAGE_LENGTH, HEADER_VALUE

# --- Конфигурация ---
# Задаем адрес сервера (0.0.0.0 для доступа извне, если IP известен)
SERVER_ADDRESS = ('192.168.0.221', 31415) # Обновите, если нужно
# --------------------

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(1)
    print(f"Сервер запущен на {SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}, ожидаем ОДНОГО клиента...")

    connection = None
    client_address = None

    try:
        while True:
            if connection is None:
                print("Ждём подключения клиента...")
                connection, client_address = server_socket.accept()
                print(f"Подключён клиент {client_address}")
                # Устанавливаем таймаут для соединения (опционально)
                connection.settimeout(10)

            try:
                # --- Пример данных для отправки ---
                # В реальности, эти значения будут меняться (например, от GUI)
                current_time = time.time()
                linear_speed = 1.0 + (current_time % 5) / 10.0  # Пример изменения
                angular_speed = 0.5 - (current_time % 3) / 10.0 # Пример изменения
                servo_positions = [int(32767 + 32767 * ((i + current_time) % 10) / 10) for i in range(12)] # Пример изменения
                lift_height = int(32767 + 32767 * (current_time % 2)) # Пример изменения
                reserved_bytes = [int(current_time) % 256] * 10 # Пример изменения

                # --- Упаковка сообщения ---
                message_to_send = pack_message(linear_speed, angular_speed, servo_positions, lift_height, reserved_bytes)
                if message_to_send is None:
                     print("Ошибка упаковки сообщения. Пропуск отправки.")
                     continue # Попробуем снова на следующей итерации

                # --- Отправка сообщения ---
                connection.sendall(message_to_send) # sendall гарантирует отправку всех байт
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Отправлено сообщение ({len(message_to_send)} байт) клиенту {client_address}")
                # print(f"   Данные: {linear_speed:.2f}, {angular_speed:.2f}, {servo_positions[:3]}..., {lift_height}, ...") # Лог первых значений

                # --- Ожидание перед следующей отправкой (например, 100 мс) ---
                time.sleep(0.1)

            except socket.timeout:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Таймаут соединения с {client_address}. Закрываем.")
                connection.close()
                connection = None
                client_address = None
            except socket.error as e:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка соединения с {client_address}: {e}. Закрываем.")
                connection.close()
                connection = None
                client_address = None
            except Exception as e:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Неожиданная ошибка при отправке: {e}. Закрываем.")
                connection.close()
                connection = None
                client_address = None


    except KeyboardInterrupt:
        print("\nПолучен сигнал остановки (Ctrl+C).")
    except Exception as e:
        print(f"Ошибка сервера: {e}")
    finally:
        if connection:
            try:
                connection.close()
                print("Соединение с клиентом закрыто.")
            except:
                pass
        try:
            server_socket.close()
            print("Серверный сокет закрыт.")
        except:
            pass

if __name__ == "__main__":
    main()
