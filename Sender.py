import time, random
from packet import Packet

class Sender:
    def __init__(self, socket, addr):
        self.socket = socket
        self.addr = addr
        self.nextseqnum = 0
        self.timer_start = None

    def connect(self):
        print("Sender: ready (RDT 3.0).")

    def start_timer(self):
        self.timer_start = time.time()

    def stop_timer(self):
        self.timer_start = None

    def timer_expired(self):
        # If the sender does not receive an ACK within 2 second, it will resend the packet.
        return (self.timer_start is not None and
                time.time() - self.timer_start > 2.0)

    def udt_send(self, pkt):
        raw = pkt.encode()

        # LOSS SIMULATION
        # There is a 30% chance that the packet is "lost"
        if random.random() < 0.3:
            print("SIMULATING PACKET LOSS (DROPPING PACKET ON PURPOSE)")
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

    def rdt_send(self, data):
        pkt = Packet(seq=self.nextseqnum, payload=data)

        while True:
            # Send packet
            self.udt_send(pkt)
            print(f"Sender: sent seq={pkt.seq}")

            # Start timer
            self.start_timer()

            while True:
                resp = self.udt_rcv()

                # Check timeout
                if self.timer_expired():
                    print("Sender: TIMEOUT → RESEND")
                    break   # break inner loop → resend

                # No ACK yet
                if resp is None:
                    continue

                # Corrupted ACK
                if resp.checksum != resp.compute_checksum():
                    print("Sender: corrupted ACK → ignore")
                    continue

                # Correct ACK
                if resp.ack == self.nextseqnum:
                    print(f"Sender: got ACK{resp.ack}")
                    self.stop_timer()
                    self.nextseqnum = 1 - self.nextseqnum
                    return

