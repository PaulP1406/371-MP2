from packet import Packet

class Receiver:
    def __init__(self, socket):
        self.sock = socket
        self.expectedseqnum = 0

    # ------------------------------------------------------------
    #  HANDSHAKE (SYN → SYN-ACK → ACK)
    # ------------------------------------------------------------
    def accept(self):
        print("Receiver: waiting for handshake...")

        # Step 1: Wait for SYN
        while True:
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"SYN":
                print("Receiver: RECEIVED SYN")
                break

        # Step 2: Send SYN-ACK
        synack = Packet(seq=0, ack=0, payload=b"SYN-ACK")
        self.udt_send(synack)
        print("Receiver: SENT SYN-ACK")

        # Step 3: Wait for ACK
        while True:
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"ACK":
                print("Receiver: RECEIVED final ACK — connection established")
                break

        # Reset state
        self.expectedseqnum = 0
    # ------------------------------------------------------------


    def udt_send(self, pkt):
        raw = pkt.encode()
        self.sock.sendto(raw, self.sender_addr)

    def udt_rcv(self):
        try:
            raw, addr = self.sock.recvfrom(4096)
            self.sender_addr = addr
            return Packet.decode(raw)
        except BlockingIOError:
            return None
        except OSError:
            return None

    def rdt_rcv(self):
        pkt = self.udt_rcv()
        if pkt is None:
            return

        # Check corruption
        if pkt.checksum != pkt.compute_checksum():
            print("Receiver: corrupted → resend last ACK")
            ack = Packet(ack=self.expectedseqnum - 1)
            self.udt_send(ack)
            return

        # In-order packet
        if pkt.seq == self.expectedseqnum:
            print(f"Receiver: received seq={pkt.seq} (in-order)")
            self.deliver_data(pkt.payload)

            ack = Packet(ack=pkt.seq)
            self.udt_send(ack)

            self.expectedseqnum += 1

        # Out-of-order
        else:
            print(f"Receiver: received out-of-order seq={pkt.seq}, expected={self.expectedseqnum}")
            ack = Packet(ack=self.expectedseqnum - 1)
            self.udt_send(ack)

    def deliver_data(self, data):
        print("Delivered:", data)
