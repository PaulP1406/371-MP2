class Packet:
    # b"" means bytes literal (not string)
    def __init__(self, seq=0, ack=0, payload=b"", checksum=0):
        self.payload = payload
        self.checksum = checksum
        self.seq = seq
        self.ack = ack

    # Compute checksum over seq, ack, and payload
    def compute_checksum(self):
        return (sum(self.payload) + self.seq + self.ack) % 256

    # Convert packet to bytes to send over UDP
    def encode(self):
        # calculate checksum
        self.checksum = self.compute_checksum()

        # encode format:
        # [ checksum | seq | ack | payload ]
        header = bytes([self.checksum, self.seq, self.ack])
        return header + self.payload

    # Convert bytes → Packet object
    @staticmethod
    def decode(data):
        checksum = data[0]
        seq = data[1]
        ack = data[2]
        payload = data[3:]
        return Packet(seq=seq, ack=ack, payload=payload, checksum=checksum)
