import socket
import time
from sender import Sender

# Configuration
RECEIVER_ADDR = ('127.0.0.1', 5000)
SENDER_ADDR   = ('127.0.0.1', 5001)

def test_retransmission():

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(SENDER_ADDR)
    sock.setblocking(False)
    
    sender = Sender(sock, RECEIVER_ADDR, window_size=10)
    
    try:
        sender.connect()
        print("\n--- Connection Established ---\n")

        total_packets = 20
        print(f"Sending {total_packets} packets rapidly to trigger loss recovery...\n")
        
        for i in range(total_packets):
            msg = f"MSG_{i}".encode()
            sender.rdt_send(msg)
            time.sleep(0.01) 
            
        print("\n--- Finished Sending (Waiting for Retransmissions) ---\n")
        
        # Wait to ensure all retransmissions complete
        time.sleep(5) 
        
        print(f"Final Base: {sender.base} (Should be {total_packets})")
        
        if sender.base == total_packets:
            print("SUCCESS: All packets delivered despite drops.")
        else:
            print("FAILURE: Some packets were never ACKed.")

        sender.close()

    except Exception as e:
        print(f"Test Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    test_retransmission()