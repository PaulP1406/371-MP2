from packet import Packet
import time
import random

# Receiver settings
LOSS_PROB = 0.3  # 30% chance to ignore a packet

class Receiver:
    def __init__(self, socket):
        self.sock = socket
        self.sender_addr = None
        self.expectedseqnum = 0 
        self.buffer_capacity = 8
        self.buffer_occupancy = 0
        self.state = "CLOSED"

    def accept(self):
        print("Receiver: waiting for handshake...")
        self.state = "LISTEN"
        timeout = time.time() + 30.0
        while True:
            if time.time() > timeout:
                return False
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"SYN":
                self.state = "SYN_RECEIVED"
                break

        synack = Packet(payload=b"SYN-ACK")
        self.udt_send(synack)

        timeout = time.time() + 5.0
        while True:
            if time.time() > timeout:
                self.udt_send(synack)
                timeout = time.time() + 5.0
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"ACK":
                print("Receiver: Connection established")
                self.state = "ESTABLISHED"
                break

        self.expectedseqnum = 0
        self.buffer_occupancy = 0
        return True

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

    def rdt_rcv(self):
        pkt = self.udt_rcv()
        if pkt is None:
            return

        # --- NEW: SIMULATE LOSS HERE ---
        # Wireshark has already seen the packet, but we pretend we didn't.
        # We generally do NOT drop handshake/control packets for stability.
        is_control = pkt.payload in [b"SYN", b"SYN-ACK", b"ACK", b"FIN"]
        
        if not is_control and random.random() < LOSS_PROB:
            print(f"Receiver: [SIMULATED LOSS] Ignoring seq={pkt.seq} (Will force timeout)")
            return  # Drop!
        # -------------------------------

        if pkt.payload == b"FIN":
            self.state = "CLOSE_WAIT"
            ack = Packet(payload=b"ACK")
            self.udt_send(ack)
            fin = Packet(payload=b"FIN")
            self.udt_send(fin)
            self.state = "LAST_ACK"
            
            timeout = time.time() + 5.0
            while True:
                if time.time() > timeout:
                    self.udt_send(fin)
                    timeout = time.time() + 5.0
                pkt2 = self.udt_rcv()
                if pkt2 and pkt2.payload == b"ACK":
                    self.state = "CLOSED"
                    print("Receiver: Connection closed")
                    break
            return

        if self.state != "ESTABLISHED":
            return

        if pkt.checksum != pkt.compute_checksum():
            print("Receiver: corrupted packet → resend last ACK")
            last_ack_num = self.expectedseqnum - 1
            available = self.buffer_capacity - self.buffer_occupancy
            nak = Packet(ack=last_ack_num, rwnd=available)
            self.udt_send(nak)
            return

        if pkt.seq == self.expectedseqnum:
            print(f"Receiver: received seq={pkt.seq} (in-order)")
            self.buffer_occupancy = min(self.buffer_capacity, self.buffer_occupancy + 1)
            self.deliver_data(pkt.payload)
            self.buffer_occupancy = max(0, self.buffer_occupancy - 1)
            available = self.buffer_capacity - self.buffer_occupancy

            ack = Packet(ack=pkt.seq, rwnd=available)
            self.udt_send(ack)
            self.expectedseqnum += 1
            return
        else:
            print(f"Receiver: out-of-order seq={pkt.seq}, expected={self.expectedseqnum}")
            last_ack_num = self.expectedseqnum - 1
            available = self.buffer_capacity - self.buffer_occupancy
            ack = Packet(ack=last_ack_num, rwnd=available)
            self.udt_send(ack)
            return

    def deliver_data(self, data):
        print("Delivered:", data)