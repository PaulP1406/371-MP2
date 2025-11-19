class Packet:
    def __init__(self, seq=0, ack=0, rwnd=0, payload=b"", checksum=0):
        self.seq = seq
        self.ack = ack
        self.rwnd = rwnd
        self.payload = payload
        self.checksum = checksum

    # simple checksum
    def compute_checksum(self):
        return (sum(self.payload) + self.seq + self.ack + self.rwnd) % 256

    # Convert packet → bytes
    def encode(self):
        self.checksum = self.compute_checksum()
        return (
            self.checksum.to_bytes(1, "big") +
            bytes([self.seq]) +
            bytes([self.ack]) +
            self.rwnd.to_bytes(2, "big") +   # 2 bytes for rwnd
            self.payload
        )

    # Convert bytes → Packet
    @staticmethod
    def decode(data):
        checksum = data[0]
        seq = data[1]
        ack = data[2]
        rwnd = int.from_bytes(data[3:5], "big")  # 2 bytes
        payload = data[5:]
        return Packet(seq=seq, ack=ack, rwnd=rwnd, payload=payload, checksum=checksum)
