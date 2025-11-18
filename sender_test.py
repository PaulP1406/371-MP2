import socket
from sender import Sender

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)

sender = Sender(sock, ("localhost", 5000))
sender.connect()

messages = [b"A", b"B", b"C", b"D"]

for m in messages:
    sender.rdt_send(m)
