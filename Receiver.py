from packet import Packet
from utils import compute_checksum

class Receiver:
    def __init__(self, socket):
        self.sock = socket

    # ---- Connection Setup (RDT 2.0 has no handshake) ---- #
    def accept(self):
        print("Receiver: ready to receive (RDT 2.0 - no handshake).")

    # ---- Reliable Data Receiving ---- #
    def rdt_rcv(self):
        pkt = self.udt_rcv()   # receive raw packet

        if not pkt:
            return

        # 1. Check if corrupted
        if pkt.checksum != compute_checksum(pkt.payload):
            print("Receiver: packet corrupted → sending NAK")
            nak = Packet(payload=b"NAK")
            self.udt_send(nak)
            return

        # 2. If correct, deliver to application
        print("Receiver: packet OK → delivering data")
        self.deliver_data(pkt.payload)

        # 3. Send ACK
        ack = Packet(payload=b"ACK")
        self.udt_send(ack)

    # ---- Deliver to application ---- #
    def deliver_data(self, data):
        print("Delivered to application:", data)

    # ---- Unreliable Send (no loss simulation yet) ---- #
    def udt_send(self, packet):
        raw = packet.encode()
        self.sock.sendto(raw, ("localhost", 0))  # replace with sender address later

    # ---- Unreliable Receive ---- #
    def udt_rcv(self):
        try:
            raw, addr = self.sock.recvfrom(4096)
            pkt = Packet.decode(raw)
            return pkt
        except BlockingIOError:
            return None

    # ---- Closing Connection (RDT 2.0 has no FIN/ACK) ---- #
    def close(self):
        print("Receiver: connection closed (RDT 2.0 has no teardown).")
