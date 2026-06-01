import socket

# Адрес и порт сервера
SERVER_ADDRESS = ('77.37.184.204', 31415)

# Создаём сокет
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Подключаемся к серверу
s.connect(SERVER_ADDRESS)

# Отправляем данные
s.send(b'Hello, World!')

# Получаем ответ
data = s.recv(1024)
# Закрываем сокет
s.close()

print(f"Полученные данные: {data.decode('utf-8')}")
