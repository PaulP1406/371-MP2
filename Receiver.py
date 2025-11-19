from packet import Packet

class Receiver:
    def __init__(self, socket):
        self.sock = socket

        # Expected next sequence number (GBN)
        self.expectedseqnum = 0

        # Flow control state
        self.buffer_capacity = 8       # Receiver buffer size
        self.buffer_occupancy = 0      # Current usage of receiver buffer

    # =====================================================
    #                  HANDSHAKE (3-way)
    # =====================================================
    def accept(self):
        print("Receiver: waiting for handshake...")

        # Step 1: receive SYN
        while True:
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"SYN":
                print("Receiver: RECEIVED SYN")
                break

        # Step 2: send SYN-ACK
        synack = Packet(payload=b"SYN-ACK")
        self.udt_send(synack)
        print("Receiver: SENT SYN-ACK")

        # Step 3: wait for ACK
        while True:
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"ACK":
                print("Receiver: RECEIVED final ACK — connection established")
                break

        # Reset receiver state
        self.expectedseqnum = 0
        self.buffer_occupancy = 0


    # =====================================================
    #                 UNRELIABLE SEND/RECV
    # =====================================================
    def udt_send(self, pkt):
        raw = pkt.encode()
        self.sock.sendto(raw, self.sender_addr)

    def udt_rcv(self):
        try:
            raw, addr = self.sock.recvfrom(4096)
            self.sender_addr = addr
            return Packet.decode(raw)
        except (BlockingIOError, OSError):
            return None


    # =====================================================
    #                  GBN RECEIVE LOGIC
    # =====================================================
    def rdt_rcv(self):
        pkt = self.udt_rcv()
        if pkt is None:
            return

        # ----- Check for corruption -----
        if pkt.checksum != pkt.compute_checksum():
            print("Receiver: corrupted packet → resend last ACK")
            last_ack_num = self.expectedseqnum - 1
            available = self.buffer_capacity - self.buffer_occupancy

            nak = Packet(ack=last_ack_num, rwnd=available)
            self.udt_send(nak)
            return


        # ----- Correct in-order packet -----
        if pkt.seq == self.expectedseqnum:
            print(f"Receiver: received seq={pkt.seq} (in-order)")

            # "Store" then deliver
            self.buffer_occupancy = max(0, self.buffer_occupancy - 1)

            self.deliver_data(pkt.payload)

            # Calculate remaining buffer space
            available = self.buffer_capacity - self.buffer_occupancy

            # Send ACK(seq)
            ack = Packet(ack=pkt.seq, rwnd=available)
            self.udt_send(ack)

            self.expectedseqnum += 1
            return


        # ----- OUT-OF-ORDER PACKET (GBN must drop it) -----
        else:
            print(f"Receiver: out-of-order seq={pkt.seq}, expected={self.expectedseqnum}")

            last_ack_num = self.expectedseqnum - 1
            available = self.buffer_capacity - self.buffer_occupancy

            # Resend last ACK
            ack = Packet(ack=last_ack_num, rwnd=available)
            self.udt_send(ack)
            return


    # =====================================================
    def deliver_data(self, data):
        print("Delivered:", data)
