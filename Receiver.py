from packet import Packet

class Receiver:
    def __init__(self, socket):
        self.sock = socket
        self.expectedseqnum = 0    # alternating-bit receiver state
        self.sender_addr = None    # will be filled after first packet

    # ---- Connection Setup ---- #
    def accept(self):
        print("Receiver: ready to receive (RDT 2.1 - no handshake).")

    # ---- Reliable Data Receiving ---- #
    def rdt_rcv(self):
        pkt = self.udt_rcv()
        if pkt is None:
            return

        # 1. Check corruption
        if pkt.checksum != pkt.compute_checksum():
            print(f"Receiver: CORRUPTED packet → send NAK{self.expectedseqnum}")
            nak = Packet(ack=self.expectedseqnum, payload=b"NAK")
            self.udt_send(nak)
            return

        # 2. Correct AND expected sequence number
        if pkt.seq == self.expectedseqnum:
            print(f"Receiver: got expected seq={pkt.seq} → delivering")
            self.deliver_data(pkt.payload)

            ack = Packet(ack=pkt.seq, payload=b"ACK")
            self.udt_send(ack)

            # flip expected sequence number
            self.expectedseqnum = 1 - self.expectedseqnum

        # 3. Duplicate old packet (seq != expectedseqnum)
        else:
            print(f"Receiver: DUPLICATE pkt seq={pkt.seq}, expected={self.expectedseqnum}")
            # Send ACK for last correctly delivered packet
            last_good_seq = 1 - self.expectedseqnum
            ack = Packet(ack=last_good_seq, payload=b"ACK")
            self.udt_send(ack)

    # ---- Deliver to application ---- #
    def deliver_data(self, data):
        print("Delivered to application:", data)

    # ---- Unreliable Send ---- #
    def udt_send(self, packet):
        raw = packet.encode()
        self.sock.sendto(raw, self.sender_addr)

    # ---- Unreliable Receive ---- #
    def udt_rcv(self):
        try:
            raw, addr = self.sock.recvfrom(4096)
            pkt = Packet.decode(raw)
            # remember sender address for replies and return only the Packet
            self.sender_addr = addr
            return pkt
        except BlockingIOError:
            return None

    # ---- Closing ---- #
    def close(self):
        print("Receiver: connection closed (RDT 2.1 - no teardown).")
