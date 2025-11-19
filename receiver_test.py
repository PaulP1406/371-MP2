import socket
from receiver import Receiver

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("localhost", 5000))
sock.setblocking(False)

receiver = Receiver(sock)

# ✔ ADD THIS
receiver.accept()  # <-- Perform handshake first

# ✔ After handshake, start receiving data
while True:
    receiver.rdt_rcv()
