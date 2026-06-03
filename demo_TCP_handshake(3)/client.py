import socket
import time
import select # Для неблокирующего чтения данных

# --- Конфигурация ---
# Адрес и порт сервера (белый IP компа, к которому подключается модем/роутер)
SERVER_ADDRESS = ('77.37.184.204', 31415) # Используй свой белый IP и порт
RECONNECT_DELAY = 5  # Время ожидания перед повторной попыткой (в секундах)
HANDSHAKE_MESSAGE = "HELLO_FROM_RPI"
WELCOME_MESSAGE = "WELCOME_RPI"
# --------------------

def attempt_connection_and_maintain_session():
    """
    Попытка подключения, выполнение handshake,
    и поддержание постоянной сессии с получением команд и отправкой подтверждений.
    """
    s = None
    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Попытка подключения к {SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}...")
        # Создаём сокет
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Устанавливаем таймаут на connect (опционально, но рекомендуется)
        s.settimeout(10)

        # Подключаемся к серверу
        s.connect(SERVER_ADDRESS)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Подключено к серверу!")

        # --- Handshake ---
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Отправка handshake '{HANDSHAKE_MESSAGE}'...")
        s.send(HANDSHAKE_MESSAGE.encode('utf-8') + b'\n') # Отправляем с символом окончания строки

        # Ждём подтверждение от сервера
        ready = select.select([s], [], [], 5.0) # Ждём до 5 секунд
        if ready[0]:
            welcome_response = s.recv(1024).decode('utf-8', errors='ignore').strip()
            if welcome_response == WELCOME_MESSAGE:
                 print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Handshake успешен! Получено: {welcome_response}")
            else:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка handshake: ожидалось '{WELCOME_MESSAGE}', получено '{welcome_response}'")
                return False # Завершаем сессию с ошибкой
        else:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Таймаут ожидания подтверждения handshake от сервера.")
            return False # Завершаем сессию с ошибкой
        # -----------------

        # --- Установка сокета в неблокирующий режим ---
        s.setblocking(False)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Установлен неблокирующий режим для сокета.")

        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Сессия установлена. Ожидание команд...")

        # --- Основной цикл обмена данными ---
        while True:
            # 1. Проверяем наличие данных от сервера (аналог serial.available())
            ready = select.select([s], [], [], 0.0) # Нулевой таймаут - проверяем немедленно
            if ready[0]: # Если сокет готов к чтению
                try:
                    raw_data = s.recv(1024)
                    if raw_data:
                        received_message = raw_data.decode('utf-8', errors='ignore').strip()
                        # --- Обработка полученной команды ---
                        if received_message.startswith("SPEED_CMD:"):
                            # Извлекаем команду скорости
                            speeds_part = received_message[len("SPEED_CMD:"):]
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Получены целевые скорости: {speeds_part}")
                            # Здесь можно выполнить логику обработки скорости для робота
                            # ...
                            
                            # --- Отправка подтверждения ---
                            confirmation_msg = f"CONFIRM_SPEED:{speeds_part}"
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Отправка подтверждения: {confirmation_msg}")
                            s.send(confirmation_msg.encode('utf-8') + b'\n')
                        else:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Получено неизвестное сообщение: {received_message}")
                        # ----------------------------------
                    else:
                        # Сервер закрыл соединение
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Сервер закрыл соединение.")
                        return False # Завершаем сессию
                except socket.error as e:
                    # Ошибка при чтении (например, разрыв)
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка при чтении данных: {e}")
                    return False # Завершаем сессию
            # Если данных нет (ready[0] пустой), просто продолжаем цикл

            # 2. Здесь можно добавить логику отправки телеметрии, если нужно
            # time.sleep(0.1) # Небольшая задержка, чтобы не перегружать CPU

    except socket.timeout:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Таймаут подключения к {SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}.")
        return False
    except ConnectionRefusedError:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Подключение отклонено сервером {SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}.")
        return False
    except socket.error as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка подключения/сессии: {e}")
        return False
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Неожиданная ошибка: {e}")
        return False
    finally:
        # Закрываем сокет в любом случае (если он был создан)
        if s:
            try:
                s.close()
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Сокет закрыт.")
            except:
                pass # Игнорируем ошибки при закрытии


if __name__ == "__main__":
    reconnect_attempts = 0
    connected = False

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Запуск клиента...")

    while True: # Бесконечный цикл для переподключений
        if attempt_connection_and_maintain_session():
            # Эта ветка не должна сюда попасть при нормальной работе сессии,
            # так как основной цикл while True внутри функции должен работать всегда,
            # пока не произойдёт ошибка или разрыв.
            # Однако, если функция возвращает True (например, после обработки особого сообщения),
            # можно выполнить действия, например, перезапустить сессию.
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Сессия завершена неожиданно (функция вернула True).")
            # reconnect_attempts = 0 # Сбрасываем счётчик? Или нет?
            # continue # Продолжить попытку подключиться
        else:
            # Если произошла ошибка подключения/сессии (функция вернула False)
            connected = False
            reconnect_attempts += 1
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Попытка #{reconnect_attempts} не удалась.")

            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ждём {RECONNECT_DELAY} секунд перед следующей попыткой...")
            time.sleep(RECONNECT_DELAY)
