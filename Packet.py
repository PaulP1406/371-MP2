class Packet:
    # b"" means we are creating byte instead of string
    def __init__(self, seq=0, ack=0, flags=0, rwnd=0, payload=b""):
        self.payload = payload

    def encode(self):
        return self.payload

    def decode(data):
        return Packet(payload=data)
