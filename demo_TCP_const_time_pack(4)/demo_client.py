import socket
import struct

# --- Конфигурация ---
SERVER_ADDRESS = ('77.37.184.204', 31415) # Используй свой белый IP и порт
ORDER = '<' # Порядок байтов (Little-Endian), должен совпадать с сервером
MESSAGE_FORMAT = f'{ORDER}HffHHHHHHHHHHHHHHHHHHHHBHBBBBBBBBBB' # Формат сообщения (46 байт)
# --------------------

try:
    # Создаём и подключаем сокет
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(SERVER_ADDRESS)
    print(f"Подключено к {SERVER_ADDRESS}")

    # Получаем ровно 46 байт
    data = b''
    while len(data) < 46:
        chunk = s.recv(46 - len(data))
        if not chunk:
            raise ConnectionError("Соединение закрыто сервером до получения полных данных")
        data += chunk

    print(f"Получено {len(data)} байт.")

    # Распаковываем
    unpacked = struct.unpack(MESSAGE_FORMAT, data)

    # Извлекаем данные
    header = unpacked[0]
    lin_speed = unpacked[1]
    ang_speed = unpacked[2]
    servo_positions = unpacked[3:15] # 12 значений
    lift_height = unpacked[15]
    reserved = unpacked[16:] # 10 значений

    # Выводим
    print("--- Распакованные данные ---")
    print(f"Заголовок (Header): 0x{header:04X}")
    print(f"Линейная скорость: {lin_speed}")
    print(f"Угловая скорость: {ang_speed}")
    print(f"Позиции серв: {list(servo_positions)}")
    print(f"Высота подъёмника: {lift_height}")
    print(f"Резервные байты: {list(reserved)}")
    print("----------------------------")

except socket.error as e:
    print(f"Ошибка сокета: {e}")
except struct.error as e:
    print(f"Ошибка распаковки struct: {e}")
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
