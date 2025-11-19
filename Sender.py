import time
import random
from packet import Packet

LOSS_PROB = 0.3
TIMEOUT_INTERVAL = 1.0

class Sender:
    def __init__(self, socket, addr, window_size=4):
        self.socket = socket
        self.addr = addr

        self.window_size = window_size
        self.base = 0
        self.nextseqnum = 0
        self.sent_packets = {}

        self.timer_start = None

    # ------------------------------------------------------------
    #  HANDSHAKE (SYN → SYN-ACK → ACK)
    # ------------------------------------------------------------
    def connect(self):
        print("Sender: initiating handshake...")

        # Step 1: Send SYN
        syn = Packet(seq=0, ack=0, payload=b"SYN")
        self.udt_send(syn)
        print("Sender: SENT SYN")

        # Step 2: Wait for SYN-ACK
        while True:
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"SYN-ACK":
                print("Sender: RECEIVED SYN-ACK")
                break

        # Step 3: Send final ACK
        ack = Packet(seq=0, ack=0, payload=b"ACK")
        self.udt_send(ack)
        print("Sender: SENT ACK — connection established")

        # Reset state
        self.base = 0
        self.nextseqnum = 0
    # ------------------------------------------------------------


    # Timer controls
    def start_timer(self):
        self.timer_start = time.time()

    def stop_timer(self):
        self.timer_start = None

    def timer_expired(self):
        return (self.timer_start is not None and
                time.time() - self.timer_start > TIMEOUT_INTERVAL)

    # Unreliable send
    def udt_send(self, pkt):
        raw = pkt.encode()

        if random.random() < LOSS_PROB:
            print("DROPPING PACKET ON PURPOSE")
            return

        self.socket.sendto(raw, self.addr)

    def udt_rcv(self):
        try:
            raw, _ = self.socket.recvfrom(4096)
            return Packet.decode(raw)
        except BlockingIOError:
            return None
        except OSError:
            return None

    # Main Go-Back-N send
    def rdt_send(self, data):
        # Window full → wait
        while self.nextseqnum >= self.base + self.window_size:
            resp = self.udt_rcv()
            if resp:
                self._process_ack(resp)
            if self.timer_expired():
                self._timeout_resend()

        # Create packet
        pkt = Packet(seq=self.nextseqnum, payload=data)

        # Send packet
        self.udt_send(pkt)
        print(f"Sender: sent seq={pkt.seq}")

        # Store packet for future resending
        self.sent_packets[self.nextseqnum] = pkt

        # Start timer if this is the first in window
        if self.base == self.nextseqnum:
            self.start_timer()

        self.nextseqnum += 1

        # Wait for ACKs & timeouts
        while True:
            resp = self.udt_rcv()
            if resp:
                self._process_ack(resp)

            # All packets ACKed
            if self.base == self.nextseqnum:
                return

            if self.timer_expired():
                self._timeout_resend()

    # Handle ACK from receiver
    def _process_ack(self, pkt):
        if pkt.checksum != pkt.compute_checksum():
            print("Sender: corrupted ACK → ignore")
            return

        print(f"Sender: got cumulative ACK {pkt.ack}")

        self.base = pkt.ack + 1

        if self.base == self.nextseqnum:
            self.stop_timer()
        else:
            self.start_timer()

    # retransmit all packets in window
    def _timeout_resend(self):
        print("Sender: TIMEOUT → RESEND WINDOW")

        self.start_timer()

        for seq in range(self.base, self.nextseqnum):
            pkt = self.sent_packets[seq]
            print(f"Sender: resending seq={seq}")
            self.udt_send(pkt)
