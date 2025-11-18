import Packet

def make_pkt(self,data):
        return Packet(payload=data)

class Sender:
    def __init__(self, socket, addr):
        self.socket = socket
        self.addr = addr
    
    # Helper method
    
    
    # ---- Connection Setup ---- #
    def connect(self):
        pass

    # ---- Reliable Data Transfer ---- #
    def rdt_send(self, data):
        make_pkt(data)
        pass

    # (Optional) Break data into segments
    def split_into_segments(self, data):
        pass

    # ---- Window / ACK Handling ---- #
    def handle_ack(self, pkt):
        pass

    # ---- Unreliable Channel Simulation ---- #
    def udt_send(self, packet):
        pass

    def udt_rcv(self):
        pass

    # ---- Timer (for retransmissions) ---- #
    def start_timer(self):
        pass

    def stop_timer(self):
        pass

    def timeout(self):
        pass

    # ---- Closing Connection ---- #
    def close(self):
        pass
