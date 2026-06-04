import socket
# Импортируем наши функции и конфигурацию
from demo_protocol_utils import unpack_message, MESSAGE_LENGTH

# --- Конфигурация ---
# Адрес и порт сервера (белый IP компа, к которому подключается модем/роутер)
SERVER_ADDRESS = ('77.37.184.204', 31415) # Используй свой белый IP и порт
# --------------------

def main():
    try:
        # Создаём и подключаем сокет
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Устанавливаем таймаут (опционально)
        s.settimeout(10)
        s.connect(SERVER_ADDRESS)
        print(f"Подключено к {SERVER_ADDRESS}")

        # Получаем ровно MESSAGE_LENGTH байт
        data = b''
        while len(data) < MESSAGE_LENGTH:
            chunk = s.recv(MESSAGE_LENGTH - len(data))
            if not chunk:
                raise ConnectionError("Соединение закрыто сервером до получения полных данных")
            data += chunk

        print(f"Получено {len(data)} байт.")

        # --- Распаковка сообщения ---
        parsed_data = unpack_message(data)
        if parsed_data:
            print("--- Распакованные данные ---")
            print(f"Заголовок (Header): 0x{parsed_data['header']:04X}")
            print(f"Линейная скорость: {parsed_data['linear_speed']:.2f}")
            print(f"Угловая скорость: {parsed_data['angular_speed']:.2f}")
            print(f"Позиции серв (первые 3): {parsed_data['servo_positions'][:3]}...") # Показываем первые 3
            print(f"Высота подъёмника: {parsed_data['lift_height']}")
            print(f"Резервные байты (первые 3): {parsed_data['reserved'][:3]}...")     # Показываем первые 3
            print("---------------------------")
        else:
            print("Ошибка при распаковке сообщения.")


    except socket.timeout:
        print("Таймаут подключения/чтения.")
    except socket.error as e:
        print(f"Ошибка сокета: {e}")
    except ConnectionError as e:
        print(f"Ошибка соединения: {e}")
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
    finally:
        try:
            s.close()
            print("Сокет закрыт.")
        except:
            pass

if __name__ == "__main__":
    main()
