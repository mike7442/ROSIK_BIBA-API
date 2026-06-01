import socket

# Создаём сокет
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Привязываем сокет к адресу и порту
server_socket.bind(('192.168.0.221', 31415))

# Начинаем прослушивать входящие соединения
server_socket.listen(1)

print("Сервер запущен на порту 31415...")

while True:
    # Принимаем соединение от клиента
    client_connection, client_address = server_socket.accept()
    print(f'Подключение от {client_address}')

    # Получаем сообщение от клиента
    request = client_connection.recv(1024).decode()
    print(f'Запрос от клиента: {request}')

    # Отправляем ответ клиенту
    response = 'Привет от сервера!'
    client_connection.sendall(response.encode())

    # Закрываем соединение
    client_connection.close()
