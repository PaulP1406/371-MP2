import socket
from Sender import Sender

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(True)

sender = Sender(sock, ("localhost", 5000))

sender.connect()   # RDT 2.0 prints only

# send some bytes
sender.rdt_send(b"Hello RDT 2.0!")
