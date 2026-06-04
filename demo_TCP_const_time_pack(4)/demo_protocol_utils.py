import struct

# --- Конфигурация протокола ---
ORDER = '<'  # Порядок байтов (Little-Endian)
HEADER_VALUE = 0xDEAD # Значение стартовых 2 байт
MESSAGE_FORMAT = f'{ORDER}HffHHHHHHHHHHHHHHHHHHHHBHBBBBBBBBBB' # Формат сообщения (46 байт)
MESSAGE_LENGTH = struct.calcsize(MESSAGE_FORMAT) # Вычисляем длину: 46 байт
# ------------------------------

def pack_message(linear_speed, angular_speed, servo_positions, lift_height, reserved_bytes=None):
    """
    Упаковывает данные в байты по заданному формату протокола.

    Args:
        linear_speed (float): Линейная скорость.
        angular_speed (float): Угловая скорость.
        servo_positions (list[int]): Список из 12 значений позиций серв (0-65535).
        lift_height (int): Высота подъёмника (0-65535).
        reserved_bytes (list[int], optional): Список из 10 значений резервных байт (0-255).
                                              По умолчанию [0] * 10.

    Returns:
        bytes: Байтовое представление сообщения.
               Возвращает None, если входные данные некорректны.
    """
    if len(servo_positions) != 12:
        print(f"pack_message error: Expected 12 servo positions, got {len(servo_positions)}")
        return None
    # Проверка диапазона для серв и подъёмника (unsigned short)
    for i, pos in enumerate(servo_positions):
        if not 0 <= pos <= 65535:
            print(f"pack_message error: Servo position {i} out of range (0-65535): {pos}")
            return None
    if not 0 <= lift_height <= 65535:
        print(f"pack_message error: Lift height out of range (0-65535): {lift_height}")
        return None

    if reserved_bytes is None:
        reserved_bytes = [0] * 10
    if len(reserved_bytes) != 10:
        print(f"pack_message error: Expected 10 reserved bytes, got {len(reserved_bytes)}")
        return None
    # Проверка диапазона для резервных байт (unsigned char)
    for i, byte_val in enumerate(reserved_bytes):
        if not 0 <= byte_val <= 255:
            print(f"pack_message error: Reserved byte {i} out of range (0-255): {byte_val}")
            return None

    try:
        # Упаковываем всё за один вызов struct.pack
        packed_data = struct.pack(
            MESSAGE_FORMAT,
            HEADER_VALUE,           # 2 байта
            linear_speed,           # 4 байта (float)
            angular_speed,          # 4 байта (float)
            *servo_positions,       # 12 * 2 байта (unsigned short)
            lift_height,            # 2 байта (unsigned short)
            *reserved_bytes         # 10 * 1 байт (unsigned char)
        )
        return packed_data
    except struct.error as e:
        print(f"pack_message struct error: {e}")
        return None

def unpack_message(data):
    """
    Распаковывает байты в структурированные данные по заданному формату протокола.

    Args:
        data (bytes): Байтовое сообщение для распаковки.

    Returns:
        dict or None: Словарь с распакованными данными или None в случае ошибки.
                      {'header': int, 'linear_speed': float, 'angular_speed': float,
                       'servo_positions': list[int], 'lift_height': int, 'reserved': list[int]}
    """
    if len(data) != MESSAGE_LENGTH:
        print(f"unpack_message error: Expected {MESSAGE_LENGTH} bytes, got {len(data)}")
        return None

    try:
        unpacked = struct.unpack(MESSAGE_FORMAT, data)
    except struct.error as e:
        print(f"unpack_message struct error: {e}")
        return None

    header = unpacked[0]
    if header != HEADER_VALUE:
        print(f"unpack_message error: Expected header 0x{HEADER_VALUE:04X}, got 0x{header:04X}")
        return None

    linear_speed = unpacked[1]
    angular_speed = unpacked[2]
    servo_positions = list(unpacked[3:15])
    lift_height = unpacked[15]
    reserved = list(unpacked[16:])

    return {
        'header': header,
        'linear_speed': linear_speed,
        'angular_speed': angular_speed,
        'servo_positions': servo_positions,
        'lift_height': lift_height,
        'reserved': reserved
    }
