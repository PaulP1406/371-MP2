from Packet import Packet
from utils import compute_checksum   # <-- you will need this function

class Sender:
    def __init__(self, socket, addr):
        self.socket = socket
        self.addr = addr

    # ---- Helper Method ---- #
    def make_pkt(self, data):
        return Packet(payload=data)

    # ---- Connection Setup (RDT 2.0 has no handshake) ---- #
    def connect(self):
        print("Sender: RDT 2.0 - No connection setup required.")

    # ---- Reliable Data Transfer ---- #
    def rdt_send(self, data):
        # 1. Make packet
        pkt = self.make_pkt(data)

        # 2. Send the packet
        self.udt_send(pkt)
        print("Sender: sent data packet")

        # 3. Wait for ACK / NAK
        while True:
            response = self.udt_rcv()

            if response is None:
                continue  # keep waiting

            # Check if ACK/NAK payload matches
            if response.payload == b"ACK":
                print("Sender: ACK received → done")
                break

            elif response.payload == b"NAK":
                print("Sender: NAK received → resending...")
                self.udt_send(pkt)

    # ---- Unreliable Channel Simulation ---- #
    def udt_send(self, packet):
        raw = packet.encode()
        self.socket.sendto(raw, self.addr)

    def udt_rcv(self):
        try:
            raw, _ = self.socket.recvfrom(4096)
            pkt = Packet.decode(raw)
            return pkt
        except BlockingIOError:
            return None

    # ---- Timer (not used in RDT 2.0) ---- #
    def start_timer(self):
        pass

    def stop_timer(self):
        pass

    def timeout(self):
        pass

    # ---- Closing Connection ---- #
    def close(self):
        print("Sender: RDT 2.0 - No close required.")
