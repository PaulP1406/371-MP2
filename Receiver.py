class Receiver:
    def __init__(self, socket):
        pass

    # ---- Connection Setup ---- #
    def accept(self):
        pass

    # ---- Reliable Data Receiving ---- #
    def rdt_rcv(self):
        pass

    # Deliver to application
    def deliver_data(self, data):
        pass

    # ---- Unreliable Channel Simulation ---- #
    def udt_send(self, packet):
        pass

    def udt_rcv(self):
        pass

    # ---- Closing Connection ---- #
    def close(self):
        pass
