import time
import random
from packet import Packet

LOSS_PROB = 0.3
TIMEOUT_INTERVAL = 1.0

class Sender:
    def __init__(self, socket, addr, window_size=10):
        self.socket = socket
        self.addr = addr

        # GBN style states
        self.window_size = window_size        # sender pipeline window
        self.base = 0
        self.nextseqnum = 0
        self.sent_packets = {}

        # -flow control receiver window
        self.receiver_rwnd = 9999             # will be updated by ACKs

        # congestion control window + ssthresh
        self.cwnd = 1                         # start in slow start
        self.ssthresh = 8                     # typical initial threshold

        # Timer
        self.timer_start = None
        
        # Connection state
        self.state = "CLOSED"
        
        # Fast retransmit (TCP Reno feature)
        self.dup_ack_count = 0
        self.last_ack_received = -1

    # handshake
    def connect(self):
        print("Sender: initiating handshake...")
        self.state = "SYN_SENT"

        syn = Packet(payload=b"SYN")
        self.udt_send(syn)
        print("Sender: SENT SYN")

        # Add timeout for handshake
        handshake_timeout = time.time() + 5.0
        while True:
            if time.time() > handshake_timeout:
                print("Sender: Handshake timeout, retrying...")
                self.udt_send(syn)
                handshake_timeout = time.time() + 5.0
                
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"SYN-ACK":
                print("Sender: RECEIVED SYN-ACK")
                break

        ack = Packet(payload=b"ACK")
        self.udt_send(ack)
        print("Sender: SENT ACK — connection established")

        self.base = 0
        self.nextseqnum = 0
        self.state = "ESTABLISHED"

    # timer methods
    def start_timer(self):
        self.timer_start = time.time()

    def stop_timer(self):
        self.timer_start = None

    def timer_expired(self):
        return (self.timer_start is not None and
                time.time() - self.timer_start > TIMEOUT_INTERVAL)

    # unreliable send and receive methods
    def udt_send(self, pkt):
        raw = pkt.encode()

        # IMPORTANT: Do NOT drop handshake packets
        if pkt.payload in [b"SYN", b"SYN-ACK", b"ACK"]:
            self.socket.sendto(raw, self.addr)
            return

        # Drop only DATA packets for realistic effect 
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

    # main reliable sent methods
    def rdt_send(self, data):
        if self.state != "ESTABLISHED":
            print("Sender: ERROR - Connection not established")
            return

        # EFFECTIVE WINDOW, take the minimum of these 3:
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
        # check for corruption
        if pkt.checksum != pkt.compute_checksum():
            print("Sender: corrupted ACK → ignored")
            return  # Discard corrupted ACK, do nothing

        # checker the receiver window from the ack from receiver side
        self.receiver_rwnd = pkt.rwnd

        print(f"Sender: got ACK={pkt.ack}, rwnd={pkt.rwnd}, cwnd={self.cwnd:.2f}")

        # Duplicate ACK detection for fast retransmit
        if pkt.ack == self.last_ack_received:
            self.dup_ack_count += 1
            print(f"Sender: Duplicate ACK detected, count={self.dup_ack_count}")
            
            # Fast Retransmit on 3 duplicate ACKs
            if self.dup_ack_count == 3:
                print("Sender: FAST RETRANSMIT triggered")
                self.ssthresh = max(1, self.cwnd / 2)
                self.cwnd = self.ssthresh + 3  # Fast recovery
                
                # Retransmit the lost packet
                if self.base in self.sent_packets:
                    print(f"   Fast retransmitting seq={self.base}")
                    self.udt_send(self.sent_packets[self.base])
                return
        else:
            # New ACK received
            self.dup_ack_count = 0
            self.last_ack_received = pkt.ack

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

    # ======================================================
    #               CONNECTION TEARDOWN (FIN)
    # ======================================================
    def close(self):
        if self.state != "ESTABLISHED":
            print("Sender: Connection already closed")
            return
            
        print("Sender: Initiating connection close (FIN)...")
        self.state = "FIN_WAIT_1"
        
        # Step 1: Send FIN
        fin = Packet(payload=b"FIN")
        self.udt_send(fin)
        print("Sender: SENT FIN")
        
        # Step 2: Wait for ACK from receiver
        timeout = time.time() + 5.0
        while True:
            if time.time() > timeout:
                print("Sender: FIN timeout, retrying...")
                self.udt_send(fin)
                timeout = time.time() + 5.0
                
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"ACK":
                print("Sender: RECEIVED ACK for FIN")
                self.state = "FIN_WAIT_2"
                break
        
        # Step 3: Wait for receiver's FIN
        timeout = time.time() + 5.0
        while True:
            if time.time() > timeout:
                print("Sender: Timeout waiting for receiver FIN")
                break
                
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"FIN":
                print("Sender: RECEIVED FIN from receiver")
                self.state = "TIME_WAIT"
                break
        
        # Step 4: Send final ACK
        ack = Packet(payload=b"ACK")
        self.udt_send(ack)
        print("Sender: SENT final ACK")
        
        # TIME_WAIT state (in real TCP this would be 2*MSL, we'll use 2 seconds)
        print("Sender: Entering TIME_WAIT state (2 seconds)...")
        time.sleep(2.0)
        
        self.state = "CLOSED"
        print("Sender: Connection closed")
