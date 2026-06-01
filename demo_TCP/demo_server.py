#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

sock = socket.socket()
sock.bind(('192.168.0.221', 27182))
sock.listen(1)
conn, addr = sock.accept()

print( 'connected:', addr)


data = conn.recv(1024)
conn.send(data.upper())

conn.close()
