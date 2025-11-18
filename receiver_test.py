import socket
from receiver import Receiver

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("localhost", 5000))  # receiver listens on port 5000
sock.setblocking(True)

receiver = Receiver(sock)
receiver.accept()  

while True:
    receiver.rdt_rcv()
