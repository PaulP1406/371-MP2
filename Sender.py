import time
import random
from packet import Packet

LOSS_PROB = 0.3
TIMEOUT_INTERVAL = 1.0

class Sender:
    def __init__(self, socket, addr, window_size=10):
        self.socket = socket
        self.addr = addr

        # --- GBN State ---
        self.window_size = window_size        # sender pipeline window
        self.base = 0
        self.nextseqnum = 0
        self.sent_packets = {}

        # --- Flow Control ---
        self.receiver_rwnd = 9999             # updated by ACKs

        # --- Congestion Control ---
        self.cwnd = 1                         # start in slow start
        self.ssthresh = 8                     # typical initial threshold

        # Timer
        self.timer_start = None

    # ======================================================
    #                   HANDSHAKE
    # ======================================================
    def connect(self):
        print("Sender: initiating handshake...")

        syn = Packet(payload=b"SYN")
        self.udt_send(syn)
        print("Sender: SENT SYN")

        while True:
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"SYN-ACK":
                print("Sender: RECEIVED SYN-ACK")
                break

        ack = Packet(payload=b"ACK")
        self.udt_send(ack)
        print("Sender: SENT ACK — connection established")

        self.base = 0
        self.nextseqnum = 0

    # ======================================================
    #                    TIMER
    # ======================================================
    def start_timer(self):
        self.timer_start = time.time()

    def stop_timer(self):
        self.timer_start = None

    def timer_expired(self):
        return (self.timer_start is not None and
                time.time() - self.timer_start > TIMEOUT_INTERVAL)

    # ======================================================
    #                UNRELIABLE SEND
    # ======================================================
    def udt_send(self, pkt):
        raw = pkt.encode()

        # IMPORTANT: Do NOT drop handshake packets
        if pkt.payload in [b"SYN", b"SYN-ACK", b"ACK"]:
            self.socket.sendto(raw, self.addr)
            return

        # Drop only DATA packets
        if random.random() < LOSS_PROB:
            print("DROPPING PACKET ON PURPOSE")
            return

        self.socket.sendto(raw, self.addr)

    def udt_rcv(self):
        try:
            raw, _ = self.socket.recvfrom(4096)
            return Packet.decode(raw)
        except (BlockingIOError, OSError):
            return None

    # ======================================================
    #              MAIN SEND (GBN + FC + CC)
    # ======================================================
    def rdt_send(self, data):

        # EFFECTIVE WINDOW:
        #   pipeline limit (GBN)
        #   receiver window (flow control)
        #   congestion window (network control)
        effective_win = int(min(self.window_size,
                                self.receiver_rwnd,
                                self.cwnd))

        while (self.nextseqnum - self.base) >= effective_win:
            resp = self.udt_rcv()
            if resp:
                self._process_ack(resp)
                effective_win = int(min(self.window_size,
                                        self.receiver_rwnd,
                                        self.cwnd))
            if self.timer_expired():
                self._timeout_resend()

        # -------- Send packet --------
        pkt = Packet(seq=self.nextseqnum, payload=data)
        self.udt_send(pkt)
        print(f"Sender: sent seq={pkt.seq}, cwnd={self.cwnd:.2f}, ssthresh={self.ssthresh}")

        self.sent_packets[self.nextseqnum] = pkt

        if self.base == self.nextseqnum:
            self.start_timer()

        self.nextseqnum += 1

        # After sending, wait for ACKs / timeouts
        while True:
            resp = self.udt_rcv()
            if resp:
                self._process_ack(resp)
                return

            if self.timer_expired():
                self._timeout_resend()

    # ======================================================
    #                  PROCESS ACK
    # ======================================================
    def _process_ack(self, pkt):

        if pkt.checksum != pkt.compute_checksum():
            print("Sender: corrupted ACK → ignored")
            return

        # FLOW CONTROL
        self.receiver_rwnd = pkt.rwnd

        print(f"Sender: got ACK={pkt.ack}, rwnd={pkt.rwnd}, cwnd={self.cwnd:.2f}")

        # --- CONGESTION CONTROL LOGIC ---
        if self.cwnd < self.ssthresh:
            # Slow Start (exponential)
            self.cwnd += 1
        else:
            # Congestion Avoidance (linear)
            self.cwnd += 1 / self.cwnd

        # Move GBN window
        self.base = pkt.ack + 1

        if self.base == self.nextseqnum:
            self.stop_timer()
        else:
            self.start_timer()

    # ======================================================
    #               TIMEOUT -> MULTIPLICATIVE DECREASE
    # ======================================================
    def _timeout_resend(self):
        print("Sender: TIMEOUT → RESEND WINDOW (CONGESTION)")

        # Congestion response
        self.ssthresh = max(1, self.cwnd / 2)
        self.cwnd = 1
        print(f"   NEW cwnd={self.cwnd}, NEW ssthresh={self.ssthresh}")

        self.start_timer()

        for seq in range(self.base, self.nextseqnum):
            pkt = self.sent_packets[seq]
            print(f"   Resending seq={seq}")
            self.udt_send(pkt)
