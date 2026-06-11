import struct
import random

# ORDER = '<'  # Порядок байтов (Little-Endian)
# MESSAGE_FORMAT = f'{ORDER}HHHHHHHHHHHH' # Формат сообщения (46 байт)
# MESSAGE_LENGTH = struct.calcsize(MESSAGE_FORMAT) # Вычисляем длину: 46 байт

# list = [random.randint(0, 65535) for _ in range(12)]
# print(f"list = {list}")
# bytes_ = struct.pack(MESSAGE_FORMAT,*list)
# print(bytes_)
# print(len(bytes_))
# new_list = struct.unpack(MESSAGE_FORMAT,bytes_)
# print(f"new list = {new_list}")
header = 0XDEAD
print(header)