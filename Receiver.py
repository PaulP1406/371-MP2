from packet import Packet
import time

class Receiver:
    def __init__(self, socket):
        self.sock = socket
        self.sender_addr = None

        # Expected next sequence number (GBN)
        self.expectedseqnum = 0 

        # Flow control state
        self.buffer_capacity = 8       # Receiver buffer size
        self.buffer_occupancy = 0      # Current usage of receiver buffer
        
        # Connection state
        self.state = "CLOSED"

    # 3 way handshake
    def accept(self):
        print("Receiver: waiting for handshake...")
        self.state = "LISTEN"

        # Step 1: receive SYN
        timeout = time.time() + 30.0  # Wait up to 30 seconds for connection
        while True:
            if time.time() > timeout:
                print("Receiver: Connection timeout")
                self.state = "CLOSED"
                return False
                
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"SYN":
                print("Receiver: RECEIVED SYN")
                self.state = "SYN_RECEIVED"
                break

        # Step 2: send SYN-ACK
        synack = Packet(payload=b"SYN-ACK")
        self.udt_send(synack)
        print("Receiver: SENT SYN-ACK")

        # Step 3: wait for ACK
        timeout = time.time() + 5.0
        while True:
            if time.time() > timeout:
                print("Receiver: ACK timeout, resending SYN-ACK...")
                self.udt_send(synack)
                timeout = time.time() + 5.0
                
            pkt = self.udt_rcv()
            if pkt and pkt.payload == b"ACK":
                print("Receiver: RECEIVED final ACK — connection established")
                self.state = "ESTABLISHED"
                break

        # Reset receiver state
        self.expectedseqnum = 0
        self.buffer_occupancy = 0
        return True


    # udt send and receive
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


    # receive logic, following GBN style
    def rdt_rcv(self):
        pkt = self.udt_rcv()
        if pkt is None:
            return

        # Handle connection teardown (FIN)
        if pkt.payload == b"FIN":
            print("Receiver: RECEIVED FIN, closing connection...")
            self.state = "CLOSE_WAIT"
            
            # Send FIN-ACK
            finack = Packet(payload=b"FIN-ACK")
            self.udt_send(finack)
            print("Receiver: SENT FIN-ACK")
            
            # Send own FIN
            fin = Packet(payload=b"FIN")
            self.udt_send(fin)
            print("Receiver: SENT FIN")
            
            # Wait for final ACK
            timeout = time.time() + 2.0
            while True:
                if time.time() > timeout:
                    break
                pkt2 = self.udt_rcv()
                if pkt2 and pkt2.payload == b"ACK":
                    print("Receiver: RECEIVED final ACK — connection closed")
                    break
            
            self.state = "CLOSED"
            return

        if self.state != "ESTABLISHED":
            return

        # corruption check
        if pkt.checksum != pkt.compute_checksum():
            print("Receiver: corrupted packet → resend last ACK")
            last_ack_num = self.expectedseqnum - 1
            available = self.buffer_capacity - self.buffer_occupancy

            nak = Packet(ack=last_ack_num, rwnd=available)
            self.udt_send(nak)
            return


        # in order packet
        if pkt.seq == self.expectedseqnum:
            print(f"Receiver: received seq={pkt.seq} (in-order)")

            # Simulate buffer usage: increment when receiving, will be "consumed" by app
            self.buffer_occupancy = min(self.buffer_capacity, self.buffer_occupancy + 1)
            
            self.deliver_data(pkt.payload)
            
            # After delivery, data is consumed from buffer
            self.buffer_occupancy = max(0, self.buffer_occupancy - 1)

            # Calculate remaining buffer space
            available = self.buffer_capacity - self.buffer_occupancy

            # Send ACK(seq)
            ack = Packet(ack=pkt.seq, rwnd=available)
            self.udt_send(ack)

            self.expectedseqnum += 1
            return


        # out of order, since we're using gbn, drop the packets
        else:
            print(f"Receiver: out-of-order seq={pkt.seq}, expected={self.expectedseqnum}")

            last_ack_num = self.expectedseqnum - 1
            available = self.buffer_capacity - self.buffer_occupancy

            # Resend last ACK
            ack = Packet(ack=last_ack_num, rwnd=available)
            self.udt_send(ack)
            return


    # mock deliver data to upper layer application
    def deliver_data(self, data):
        print("Delivered:", data)
