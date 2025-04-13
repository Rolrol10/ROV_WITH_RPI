import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('', 8004))
data, addr = s.recvfrom(8192)
print(f"📡 Pi is streaming from: {addr[0]}")
