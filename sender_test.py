import socket
from sender import Sender

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)

sender = Sender(sock, ("localhost", 5000), window_size=4)

# ✔ ADD THIS
sender.connect()  # <-- Perform handshake before sending

messages = [b"A", b"B", b"C", b"D", b"E", b"F", b"G"]

for m in messages:
    sender.rdt_send(m)
