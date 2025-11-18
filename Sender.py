from packet import Packet
from utils import compute_checksum

class Sender:
    def __init__(self, socket, addr):
        self.socket = socket
        self.addr = addr
        self.nextseqnum = 0  # alternating-bit sequence number

    # ---- Helper ---- #
    def make_pkt(self, data):
        return Packet(seq=self.nextseqnum, payload=data)

    # ---- Connection Setup ---- #
    def connect(self):
        print("Sender: RDT 2.1 - No handshake required.")

    # ---- Reliable Data Transfer ---- #
    def rdt_send(self, data):

        # Create packet with current sequence number
        pkt = Packet(seq=self.nextseqnum, payload=data)

        while True:
            # 1. Send the packet
            self.udt_send(pkt)
            print(f"Sender: sent packet with seq={pkt.seq}")

            # 2. Wait for response
            response = self.udt_rcv()
            if response is None:
                continue

            # 3. Check corruption of ACK/NAK
            if response.checksum != response.compute_checksum():
                print("Sender: corrupted ACK/NAK → resend")
                continue

            # 4. If correct ACK received
            if response.payload == b"ACK" and response.ack == self.nextseqnum:
                print(f"Sender: received ACK{self.nextseqnum}")
                self.nextseqnum = 1 - self.nextseqnum  # toggle 0 ↔ 1
                break

            # 5. Otherwise (NAK or wrong seq)
            print("Sender: received NAK or wrong ACK → resend")

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

    # ---- Closing ---- #
    def close(self):
        print("Sender: RDT 2.1 - No teardown required.")
