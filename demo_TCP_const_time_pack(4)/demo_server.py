import socket
import struct
import time

# --- Конфигурация ---
SERVER_ADDRESS = ('77.37.184.204', 31415) # Используй свой белый IP и порт
HEADER = 0xDEAD # Стартовые 2 байта
ORDER = '<' # Порядок байтов (Little-Endian), можно '>'. Главное - одинаковый на сервере и клиенте
MESSAGE_FORMAT = f'{ORDER}HffHHHHHHHHHHHHHHHHHHHHBHBBBBBBBBBB' # 2 + 4 + 4 + (12 * 2) + 2 + (10 * 1) = 46 байт

# Пример данных
linear_speed = 1.5
angular_speed = 0.8
# 12 значений для серв, диапазон 0 - 65535 (unsigned short)
servo_positions = [1234, 2345, 3456, 4567, 5678, 6789, 7890, 8901, 9012, 1012, 1123, 12345]
lift_height = 4567 # Пример высоты подъёмника
reserv_bytes = [0] * 10 # 10 резервных байт, заполненных нулями (можно передавать как список)

def pack_message(header, lin_speed, ang_speed, servos, lift_h, reserv_list):
    """Упаковывает данные в байты по заданному формату."""
    # Упаковываем всё за один вызов struct.pack
    # servos передаётся как 12 аргументов
    # reserv_list распаковывается как 10 аргументов для B
    full_message = struct.pack(
        MESSAGE_FORMAT,
        header,
        lin_speed,
        ang_speed,
        *servos, # Распаковываем список позиций серв
        lift_h,
        *reserv_list # Распаковываем список резервных байт
    )
    return full_message

# --- Пример использования ---
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(SERVER_ADDRESS)
    print(f"Connected to {SERVER_ADDRESS}")

    # Упаковываем сообщение
    message_to_send = pack_message(HEADER, linear_speed, angular_speed, servo_positions, lift_height, reserv_bytes)
    print(f"Message length: {len(message_to_send)} bytes")
    print(f"Message bytes: {message_to_send}") # Для отладки

    # Отправляем
    s.sendall(message_to_send) # sendall гарантирует отправку всех байт
    print("Message sent successfully.")

    # (Опционально) Получаем ответ
    # data = s.recv(1024)
    # print(f"Received: {data.decode('utf-8', errors='ignore')}")

except socket.error as e:
    print(f"Socket error: {e}")
except struct.error as e:
    print(f"Struct packing error: {e}")
except Exception as e:
    print(f"General error: {e}")
finally:
    try:
        s.close()
        print("Socket closed.")
    except:
        pass
