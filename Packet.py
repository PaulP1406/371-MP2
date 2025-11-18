class Packet:
    def __init__(self, seq=0, ack=0, payload=b"", checksum=0):
        self.seq = seq
        self.ack = ack
        self.payload = payload
        self.checksum = checksum

    def compute_checksum(self):
        return (sum(self.payload) + self.seq + self.ack) % 256

    def encode(self):
        self.checksum = self.compute_checksum()
        return bytes([self.checksum, self.seq, self.ack]) + self.payload

    @staticmethod
    def decode(data):
        checksum = data[0]
        seq = data[1]
        ack = data[2]
        payload = data[3:]
        return Packet(seq=seq, ack=ack, payload=payload, checksum=checksum)
