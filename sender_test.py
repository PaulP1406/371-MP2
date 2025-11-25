import socket
from sender import Sender

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setblocking(False)

# Replace with the receiver's actual IP address
RECEIVER_IP = "192.168.1.100"  # Change this to receiver's IP
sender = Sender(sock, (RECEIVER_IP, 5000), window_size=4)

sender.connect()  # <-- Perform handshake before sending

messages = [b"A", b"B", b"C", b"D", b"E", b"F", b"G"]

for m in messages:
    sender.rdt_send(m)

# Close the connection properly
sender.close()
print("Sender: All messages sent and connection closed")
