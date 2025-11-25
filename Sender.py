import time
from packet import Packet

# Sender settings
TIMEOUT_INTERVAL = 1.0  # Seconds

class Sender:
    def __init__(self, socket, addr, window_size=5):
        self.socket = socket
        self.addr = addr

        # GBN style states
        self.window_size = window_size
        self.base = 0
        self.nextseqnum = 0
        self.sent_packets = {}

        # Flow control
        self.receiver_rwnd = 9999

        # Congestion control
        self.cwnd = 1
        self.ssthresh = 8

        # Timer
        self.timer_start = None
        
        # Connection state
        self.state = "CLOSED"
        
        # Fast retransmit
        self.dup_ack_count = 0
        self.last_ack_received = -1

    def connect(self):
        print("Sender: initiating handshake...")
        self.state = "SYN_SENT"

        syn = Packet(payload=b"SYN")
        self.udt_send(syn)
        print("Sender: SENT SYN")

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

    def start_timer(self):
        self.timer_start = time.time()

    def stop_timer(self):
        self.timer_start = None

    def timer_expired(self):
        return (self.timer_start is not None and
                time.time() - self.timer_start > TIMEOUT_INTERVAL)

    def check_events(self):
        # Process any pending ACKs
        resp = self.udt_rcv()
        if resp:
            self._process_ack(resp)
        
        # Check for timeout
        if self.timer_expired():
            self._timeout_resend()

    # --- CHANGED: Send EVERYTHING so Wireshark sees it ---
    def udt_send(self, pkt):
        raw = pkt.encode()
        self.socket.sendto(raw, self.addr)

    def udt_rcv(self):
        try:
            raw, _ = self.socket.recvfrom(4096)
            return Packet.decode(raw)
        except (BlockingIOError, OSError):
            return None

    def rdt_send(self, data):
        if self.state != "ESTABLISHED":
            return

        effective_win = int(min(self.window_size, self.receiver_rwnd, self.cwnd))

        while (self.nextseqnum - self.base) >= effective_win:
            resp = self.udt_rcv()
            if resp:
                self._process_ack(resp)
                effective_win = int(min(self.window_size, self.receiver_rwnd, self.cwnd))
            if self.timer_expired():
                self._timeout_resend()

        pkt = Packet(seq=self.nextseqnum, payload=data)
        self.udt_send(pkt)
        print(f"Sender: sent seq={pkt.seq}, cwnd={self.cwnd:.2f}, ssthresh={self.ssthresh}")

        self.sent_packets[self.nextseqnum] = pkt

        if self.base == self.nextseqnum:
            self.start_timer()

        self.nextseqnum += 1

        # Wait loop to process ACKs immediately after sending
        start_wait = time.time()
        while time.time() - start_wait < 0.01: # Short check
            resp = self.udt_rcv()
            if resp:
                self._process_ack(resp)
            if self.timer_expired():
                self._timeout_resend()

    def _process_ack(self, pkt):
        if pkt.checksum != pkt.compute_checksum():
            print("Sender: corrupted ACK → ignored")
            return

        self.receiver_rwnd = pkt.rwnd
        print(f"Sender: got ACK={pkt.ack}, rwnd={pkt.rwnd}, cwnd={self.cwnd:.2f}")

        if pkt.ack == self.last_ack_received:
            self.dup_ack_count += 1
            if self.dup_ack_count == 3:
                print("Sender: FAST RETRANSMIT triggered")
                self.ssthresh = max(1, self.cwnd / 2)
                self.cwnd = self.ssthresh + 3
                if self.base in self.sent_packets:
                    print(f"   Fast retransmitting seq={self.base}")
                    self.udt_send(self.sent_packets[self.base])
                return
        else:
            self.dup_ack_count = 0
            self.last_ack_received = pkt.ack

        if self.cwnd < self.ssthresh:
            self.cwnd += 1
        else:
            self.cwnd += 1 / self.cwnd

        self.base = pkt.ack + 1

        if self.base == self.nextseqnum:
            self.stop_timer()
        else:
            self.start_timer()

    def _timeout_resend(self):
        print("Sender: TIMEOUT → RESEND WINDOW (CONGESTION)")
        self.ssthresh = max(1, self.cwnd / 2)
        self.cwnd = 1
        print(f"   NEW cwnd={self.cwnd}, NEW ssthresh={self.ssthresh}")

        self.start_timer()

        for seq in range(self.base, self.nextseqnum):
            if seq in self.sent_packets:
                pkt = self.sent_packets[seq]
                print(f"   Resending seq={seq}")
                self.udt_send(pkt)

    def close(self):
        if self.state != "ESTABLISHED":
            return
            
        print("Sender: Initiating connection close (FIN)...")
        self.state = "FIN_WAIT_1"
        
        fin = Packet(payload=b"FIN")
        self.udt_send(fin)
        
        timeout = time.time() + 5.0
        while True:
            if time.time() > timeout:
                self.udt_send(fin)
                timeout = time.time() + 5.0
                
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"ACK":
                self.state = "FIN_WAIT_2"
                break
        
        timeout = time.time() + 5.0
        while True:
            if time.time() > timeout:
                break
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"FIN":
                self.state = "TIME_WAIT"
                break
        
        ack = Packet(payload=b"ACK")
        self.udt_send(ack)
        print("Sender: Connection closed")