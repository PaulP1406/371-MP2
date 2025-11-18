class Packet:
    # b"" means bytes literal (not string)
    def __init__(self, payload=b"", checksum=0):
        self.payload = payload
        self.checksum = checksum

    # Compute checksum over payload
    def compute_checksum(self):
        return sum(self.payload) % 256

    # Convert packet to bytes to send over UDP
    def encode(self):
        # calculate checksum
        self.checksum = self.compute_checksum()

        # encode format:
        # [ checksum (1 byte) | payload (remaining bytes) ]
        return self.checksum.to_bytes(1, 'big') + self.payload

    # Convert bytes → Packet object
    @staticmethod
    def decode(data):
        checksum = data[0]         # first byte
        payload = data[1:]         # rest of bytes
        return Packet(payload=payload, checksum=checksum)
