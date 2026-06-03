import socket
import time

# --- Конфигурация ---
# Адрес и порт сервера (белый IP компа)
SERVER_ADDRESS = ('77.37.184.204', 31415) # Используй свой белый IP и порт
RECONNECT_DELAY = 5  # Время ожидания перед повторной попыткой (в секундах)
MAX_RECONNECT_ATTEMPTS = 10 # Максимальное количество попыток подключения перед ожиданием (опционально)
# --------------------

def attempt_connection_and_communicate():
    """Попытка подключения, обмена данными и корректного закрытия."""
    s = None
    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Попытка подключения к {SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}...")
        # Создаём сокет
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Устанавливаем таймаут на connect/read/write (опционально, но рекомендуется)
        s.settimeout(10) 

        # Подключаемся к серверу
        s.connect(SERVER_ADDRESS)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Подключено к серверу!")

        # --- Обмен данными ---
        # Отправляем данные
        message_to_send = b'Hello, Server! This is RPi.' # Измени сообщение как нужно
        s.send(message_to_send)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Отправлено: {message_to_send.decode('utf-8', errors='ignore')}")

        # Получаем ответ (ожидаем ответ от сервера)
        try:
            data = s.recv(1024)
            if data:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Получено: {data.decode('utf-8', errors='ignore')}")
            else:
                # Сервер закрыл соединение
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Сервер закрыл соединение.")
                return False # Указывает на потерю соединения
        except socket.timeout:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Таймаут при ожидании данных от сервера.")
            return False
        except socket.error as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка получения данных: {e}")
            return False
        # --------------------

        # Если всё прошло успешно, возвращаем True
        return True

    except socket.timeout:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Таймаут подключения к {SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}.")
        return False
    except ConnectionRefusedError: # Конкретная ошибка для "Connection refused"
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Подключение отклонено сервером {SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}.")
        return False
    except socket.error as e: # Обработка других ошибок сокета (например, Host Unreachable)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ошибка подключения: {e}")
        return False
    except Exception as e: # Обработка любых других неожиданных ошибок
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

    while True: # Бесконечный цикл для переподключений
        if attempt_connection_and_communicate():
            # Если соединение и обмен прошли успешно
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Сессия завершена успешно. Ожидание перед следующим подключением...")
            reconnect_attempts = 0 # Сбрасываем счётчик попыток
            connected = True
            # Здесь можно добавить логику ожидания перед следующим обменом, если нужно
            # time.sleep(...) # Например, пауза между успешными сессиями
            # break # Если нужно выполнить только одну успешную сессию, раскомментируй
        else:
            # Если произошла ошибка подключения/обмена
            connected = False
            reconnect_attempts += 1
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Попытка #{reconnect_attempts} не удалась.")

            # Опционально: прекратить попытки после N неудач (или просто ждать бесконечно)
            if MAX_RECONNECT_ATTEMPTS > 0 and reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                 print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Достигнуто максимальное количество попыток ({MAX_RECONNECT_ATTEMPTS}). Ждём {RECONNECT_DELAY} секунд перед сбросом счётчика.")
                 # Можно сбросить счётчик или выйти, решай сам.
                 # reconnect_attempts = 0 # Сбросить счётчик и продолжить
                 # time.sleep(RECONNECT_DELAY)
                 # continue
                 # Или просто ждать дольше:
                 time.sleep(RECONNECT_DELAY)
                 continue # Продолжаем пытаться

            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ждём {RECONNECT_DELAY} секунд перед следующей попыткой...")
            time.sleep(RECONNECT_DELAY)
