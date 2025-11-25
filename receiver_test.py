import socket
import time
from receiver import Receiver


def main():
    # Create a single UDP socket for the receiver
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 5000))  # Listen on all network interfaces
    sock.setblocking(False)

    receiver = Receiver(sock)

    while True:
        if receiver.state == "CLOSED":
            ok = receiver.accept()
            if not ok:
                time.sleep(0.01)
                continue

        receiver.rdt_rcv()

        time.sleep(0.001)


if __name__ == "__main__":
    main()
