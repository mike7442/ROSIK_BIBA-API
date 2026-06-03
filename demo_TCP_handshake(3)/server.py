import socket
import time
import errno
import select # Для неблокирующего чтения

# --- Конфигурация ---
# Задаем адрес сервера (0.0.0.0 для доступа извне, если IP известен)
SERVER_ADDRESS = ('192.168.0.221', 31415)
HANDSHAKE_MESSAGE = b"HELLO_FROM_RPI\n"
WELCOME_MESSAGE = b"WELCOME_RPI\n"
CONFIRM_PREFIX = "CONFIRM_SPEED:"
COMMAND_PREFIX = "SPEED_CMD:"
HANDSHAKE_TIMEOUT = 10 # Таймаут ожидания handshake (сек)
CONFIRM_TIMEOUT = 5.0 # Таймаут ожидания подтверждения (сек)
# --------------------

def handle_client_data(data, client_address):
    """Обрабатывает полученные от клиента данные."""
    decoded_data = data.decode('utf-8', errors='ignore').strip()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{client_address}] Получено: {decoded_data}")
    # Проверяем, является ли это подтверждением
    if decoded_data.startswith(CONFIRM_PREFIX):
        received_command = decoded_data[len(CONFIRM_PREFIX):]
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{client_address}] Подтверждение получено: {received_command}")
        return received_command # Возвращаем подтверждённую команду
    else:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{client_address}] Получено неизвестное сообщение: {decoded_data}")
        return None

def send_target_speeds(connection, speeds, client_address):
    """Отправляет клиенту целевые скорости."""
    try:
        message = f"{COMMAND_PREFIX}{speeds}\n" # Пример формата команды
        connection.sendall(message.encode('utf-8'))
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{client_address}] Отправлена команда: {message.strip()}")
        return message.strip() # Возвращаем отправленную команду для отслеживания
    except socket.error as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка отправки данных клиенту {client_address}: {e}")
        raise # Возбуждаем исключение дальше для закрытия соединения

def main():
    # Настраиваем серверный сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(SERVER_ADDRESS)
    server_socket.listen(1) # Ожидаем только ОДНОГО клиента

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Сервер запущен на {SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}, ожидаем ОДНОГО клиента...")
    
    connection = None # Переменная для хранения активного соединения
    client_address = None
    handshake_done = False # Флаг для отслеживания handshake
    waiting_for_confirm = False # Флаг: ждём подтверждение
    last_sent_command = "" # Что именно отправили
    confirm_sent_time = 0 # Время отправки команды (для таймаута подтверждения)

    try:
        while True:
            # 1. Проверяем, есть ли активное соединение
            if connection is None:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ждём подключения клиента...")
                # Блокирующий accept - ждём первого (и единственного) клиента
                connection, client_address = server_socket.accept()
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Подключён клиент {client_address}")
                
                # Устанавливаем соединение в БЛОКИРУЮЩИЙ режим для handshake
                connection.setblocking(True)
                handshake_done = False # Сброс флага при новом подключении
                waiting_for_confirm = False # Сброс ожидания подтверждения
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Установлен блокирующий режим для handshake с {client_address}.")

            # 2. Если соединение есть, проверяем handshake
            if not handshake_done:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ожидание handshake от {client_address}...")
                try:
                    # Устанавливаем таймаут на recv для handshake
                    connection.settimeout(HANDSHAKE_TIMEOUT)
                    data = connection.recv(len(HANDSHAKE_MESSAGE))
                    if data == HANDSHAKE_MESSAGE:
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{client_address}] Получен handshake: {data.decode('utf-8', errors='ignore').strip()}")
                        # Отправляем подтверждение handshake
                        connection.sendall(WELCOME_MESSAGE)
                        handshake_done = True
                        # Переключаем на неблокирующий режим для основной сессии
                        connection.setblocking(False)
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{client_address}] Handshake завершён. Переключен на неблокирующий режим.")
                    else:
                         print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{client_address}] Неверное сообщение handshake: {data}")
                         # Закрываем соединение при неверном handshake
                         connection.close()
                         connection = None
                         client_address = None
                         continue
                except socket.timeout:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{client_address}] Таймаут ожидания handshake.")
                    connection.close()
                    connection = None
                    client_address = None
                    continue
                except socket.error as e:
                    # Ошибка при чтении (например, разрыв)
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка при handshake с {client_address}: {e}")
                    connection.close()
                    connection = None
                    client_address = None
                    continue
                # Возвращаемся к началу цикла, не выполняя остальную логику, пока handshake не пройдён
                continue 

            # 3. После handshake - основной цикл обработки данных и отправки команд
            # --- Проверка таймаута подтверждения ---
            if waiting_for_confirm:
                if time.time() - confirm_sent_time > CONFIRM_TIMEOUT:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{client_address}] Таймаут подтверждения для команды '{last_sent_command}'. Считаем соединение потерянным.")
                    # Закрываем соединение и сбрасываем состояние
                    connection.close()
                    connection = None
                    client_address = None
                    waiting_for_confirm = False
                    last_sent_command = ""
                    confirm_sent_time = 0
                    # Переходим к следующей итерации цикла, где будет ожидаться новое подключение
                    continue

            # --- Проверка наличия данных от клиента (аналог serial.available()) ---
            try:
                ready = select.select([connection], [], [], 0.0) # Нулевой таймаут - проверяем немедленно
                if ready[0]: # Если сокет готов к чтению
                    data = connection.recv(1024)
                    if data:
                        # Данные есть!
                        confirmed_cmd = handle_client_data(data, client_address)
                        # Проверяем, совпадает ли подтверждение с ожидаемым
                        if waiting_for_confirm and confirmed_cmd and confirmed_cmd in last_sent_command:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{client_address}] Подтверждение для '{last_sent_command}' получено.")
                            waiting_for_confirm = False
                            last_sent_command = ""
                            confirm_sent_time = 0
                        elif waiting_for_confirm and confirmed_cmd:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{client_address}] Получено НЕСОВПАДАЮЩЕЕ подтверждение '{confirmed_cmd}' для ожидаемого '{last_sent_command}'.")
                            # Возможно, стоит игнорировать или сбросить ожидание?
                            # Для простоты, игнорируем.
                    else:
                        # Клиент закрыл соединение
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{client_address}] Клиент закрыл соединение.")
                        raise ConnectionResetError("Клиент закрыл соединение")
            except BlockingIOError:
                # Нет данных для чтения - это нормально
                pass
            except socket.error as e:
                # Ошибка при чтении (например, разрыв)
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка при чтении от {client_address}: {e}")
                raise e # Возбуждаем исключение для закрытия соединения
            
            # --- Отправка команд клиенту (например, целевые скорости) ---
            # Пример: отправляем команду каждые 2 секунды (это для демонстрации)
            # В реальности, это должно быть по событию (изменение через GUI и т.п.)
            current_time = time.time()
            # Отправляем новую команду, только если не ждём подтверждения предыдущей
            if not waiting_for_confirm and current_time % 2 < 0.01: # Пример условия - каждые 2 секунды
                 target_speeds = f"L={int(current_time*10) % 100}, R={int(current_time*15) % 100}" # Пример значений
                 sent_cmd = send_target_speeds(connection, target_speeds, client_address)
                 if sent_cmd: # Если отправка прошла успешно
                     waiting_for_confirm = True
                     last_sent_command = sent_cmd
                     confirm_sent_time = time.time()
                     print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{client_address}] Установлен таймер ожидания подтверждения для: {sent_cmd}")
            
            # --- ВАЖНО: Пауза, чтобы не перегружать CPU ---
            time.sleep(0.01) 

    except KeyboardInterrupt:
        print("\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Получен сигнал остановки (Ctrl+C).")
    except (ConnectionResetError, socket.error) as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Соединение с {client_address} потеряно: {e}")
    finally:
        # Закрываем соединения при выходе
        if connection:
            try:
                connection.close()
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Соединение с клиентом {client_address} закрыто.")
            except:
                pass
        try:
            server_socket.close()
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Серверный сокет закрыт.")
        except:
            pass

if __name__ == "__main__":
    main()
