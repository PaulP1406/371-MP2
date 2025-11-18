from packet import Packet

class Receiver:
    def __init__(self, socket):
        self.sock = socket
        self.expectedseqnum = 0
        self.sender_addr = None

    def accept(self):
        print("Receiver: ready (RDT 3.0 - no handshake).")

    def rdt_rcv(self):
        pkt = self.udt_rcv()
        if pkt is None:
            return

        # Corruption
        if pkt.checksum != pkt.compute_checksum():
            print("Receiver: corrupted → ACK last good seq")
            last_good = 1 - self.expectedseqnum
            ack = Packet(ack=last_good, payload=b"ACK")
            self.udt_send(ack)
            return

        # Correct & expected
        if pkt.seq == self.expectedseqnum:
            print(f"Receiver: got expected seq={pkt.seq} → deliver")
            self.deliver_data(pkt.payload)

            ack = Packet(ack=pkt.seq, payload=b"ACK")
            self.udt_send(ack)

            self.expectedseqnum = 1 - self.expectedseqnum

        else:
            print(f"Receiver: duplicate seq={pkt.seq} → resend ACK")
            last_good = 1 - self.expectedseqnum
            ack = Packet(ack=last_good, payload=b"ACK")
            self.udt_send(ack)

    def deliver_data(self, data):
        print("Delivered:", data)

    def udt_send(self, packet):
        raw = packet.encode()
        self.sock.sendto(raw, self.sender_addr)

    def udt_rcv(self):
        try:
            raw, addr = self.sock.recvfrom(4096)
            self.sender_addr = addr
            return Packet.decode(raw)
        except BlockingIOError:
            return None
