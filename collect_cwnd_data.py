"""
CWND vs Time Data Collector for Graphing
=========================================

Runs sender and collects CWND, SSTHRESH, RWND over time with timestamps.
Outputs CSV file that can be imported into Excel, Google Sheets, or matplotlib.
"""

import socket
import time
import csv
from sender import Sender

# Test Configuration Parameters
CONFIG = {
    'LOSS_PROBABILITY': 0.3,        # 30% packet loss (from sender.py)
    'NUM_PACKETS': 100,              # Number of packets to send
    'PACKET_SIZE': 100,              # Bytes per packet
    'WINDOW_SIZE': 10,               # GBN window size
    'INITIAL_CWND': 1,               # Starting congestion window
    'INITIAL_SSTHRESH': 8,           # Initial slow start threshold
    'TIMEOUT_INTERVAL': 1.0,         # Seconds
    'RECEIVER_BUFFER': 8,            # Receiver buffer capacity
}

class CWNDDataCollector:
    """Collects CWND, SSTHRESH, RWND data over time"""
    
    def __init__(self):
        self.data_points = []
        self.start_time = None
        self.packets_sent = 0
        self.acks_received = 0
        self.retransmissions = 0
        self.timeouts = 0
        self.fast_retransmits = 0
        
    def collect_data_point(self, sender, event_type="send"):
        """Collect a single data point"""
        if self.start_time is None:
            self.start_time = time.time()
        
        timestamp = time.time() - self.start_time
        
        data_point = {
            'time': timestamp,
            'cwnd': sender.cwnd,
            'ssthresh': sender.ssthresh,
            'rwnd': sender.receiver_rwnd,
            'base': sender.base,
            'nextseqnum': sender.nextseqnum,
            'event': event_type,
            'packets_sent': self.packets_sent,
            'acks_received': self.acks_received,
        }
        
        self.data_points.append(data_point)
        
    def collect_transmission_data(self, num_packets=100, packet_size=100):
        """Send packets and collect CWND data"""
        print("\n" + "="*70)
        print("COLLECTING CWND vs TIME DATA")
        print("="*70)
        print(f"\nTest Parameters:")
        print(f"  Packets to send:     {num_packets}")
        print(f"  Packet size:         {packet_size} bytes")
        print(f"  Loss probability:    {CONFIG['LOSS_PROBABILITY']*100}%")
        print(f"  Window size:         {CONFIG['WINDOW_SIZE']}")
        print(f"  Initial CWND:        {CONFIG['INITIAL_CWND']}")
        print(f"  Initial SSTHRESH:    {CONFIG['INITIAL_SSTHRESH']}")
        print(f"  Timeout interval:    {CONFIG['TIMEOUT_INTERVAL']} sec")
        print(f"  Receiver buffer:     {CONFIG['RECEIVER_BUFFER']}")
        print("\nStarting data collection...")
        
        # Create sender
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sender = Sender(sock, ("localhost", 5000), window_size=CONFIG['WINDOW_SIZE'])
        
        # Connect
        print("Establishing connection...")
        sender.connect()
        self.collect_data_point(sender, "connect")
        
        # Send packets and collect data
        data = b'X' * packet_size
        
        print(f"\nSending {num_packets} packets...")
        
        for i in range(num_packets):
            # Collect data before send
            self.collect_data_point(sender, "before_send")
            
            # Track initial state
            initial_cwnd = sender.cwnd
            initial_base = sender.base
            
            # Send packet
            sender.rdt_send(data)
            self.packets_sent += 1
            
            # Collect data after send
            self.collect_data_point(sender, "after_send")
            
            # Track events
            if sender.base > initial_base:
                self.acks_received += 1
                self.collect_data_point(sender, "ack_received")
            
            if sender.cwnd < initial_cwnd:
                # CWND decreased - likely timeout or fast retransmit
                if sender.cwnd == 1:
                    self.timeouts += 1
                    self.collect_data_point(sender, "timeout")
                else:
                    self.fast_retransmits += 1
                    self.collect_data_point(sender, "fast_retransmit")
            
            # Progress update
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i+1}/{num_packets} packets, "
                      f"CWND={sender.cwnd:.2f}, SSTHRESH={sender.ssthresh}, "
                      f"RWND={sender.receiver_rwnd}")
        
        # Close connection
        print("\nClosing connection...")
        sender.close()
        self.collect_data_point(sender, "close")
        
        print(f"\nData collection complete!")
        print(f"  Total data points:   {len(self.data_points)}")
        print(f"  Packets sent:        {self.packets_sent}")
        print(f"  ACKs received:       {self.acks_received}")
        print(f"  Timeouts detected:   {self.timeouts}")
        print(f"  Fast retransmits:    {self.fast_retransmits}")
        
    def export_to_csv(self, filename='cwnd_data.csv'):
        """Export data to CSV file"""
        print(f"\nExporting data to {filename}...")
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['time', 'cwnd', 'ssthresh', 'rwnd', 'base', 
                         'nextseqnum', 'event', 'packets_sent', 'acks_received']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for point in self.data_points:
                writer.writerow(point)
        
        print(f"✓ Exported {len(self.data_points)} data points")
        
    def export_summary(self, filename='test_summary.txt'):
        """Export test summary and parameters"""
        print(f"\nExporting test summary to {filename}...")
        
        with open(filename, 'w') as f:
            f.write("CWND vs TIME TEST SUMMARY\n")
            f.write("="*70 + "\n\n")
            
            f.write("TEST PARAMETERS:\n")
            f.write("-"*70 + "\n")
            for key, value in CONFIG.items():
                f.write(f"{key:<25} {value}\n")
            
            f.write("\n\nTEST RESULTS:\n")
            f.write("-"*70 + "\n")
            f.write(f"{'Total packets sent:':<25} {self.packets_sent}\n")
            f.write(f"{'ACKs received:':<25} {self.acks_received}\n")
            f.write(f"{'Timeouts:':<25} {self.timeouts}\n")
            f.write(f"{'Fast retransmits:':<25} {self.fast_retransmits}\n")
            f.write(f"{'Data points collected:':<25} {len(self.data_points)}\n")
            
            if self.data_points:
                cwnd_values = [p['cwnd'] for p in self.data_points]
                f.write(f"\n\nCWND STATISTICS:\n")
                f.write("-"*70 + "\n")
                f.write(f"{'Initial CWND:':<25} {cwnd_values[0]:.2f}\n")
                f.write(f"{'Maximum CWND:':<25} {max(cwnd_values):.2f}\n")
                f.write(f"{'Final CWND:':<25} {cwnd_values[-1]:.2f}\n")
                f.write(f"{'Average CWND:':<25} {sum(cwnd_values)/len(cwnd_values):.2f}\n")
            
            f.write(f"\n\nDATA FILE:\n")
            f.write("-"*70 + "\n")
            f.write(f"CSV file: cwnd_data.csv\n")
            f.write(f"Columns: time, cwnd, ssthresh, rwnd, base, nextseqnum, event\n")
            f.write(f"\nImport this CSV into Excel, Google Sheets, or Python to create graphs.\n")
        
        print(f"✓ Summary exported")
    
    def print_graph_instructions(self):
        """Print instructions for creating graphs"""
        print("\n" + "="*70)
        print("GRAPHING INSTRUCTIONS")
        print("="*70)
        
        print("\n📊 EXCEL / GOOGLE SHEETS:")
        print("-"*70)
        print("1. Open cwnd_data.csv")
        print("2. Select columns 'time' and 'cwnd'")
        print("3. Insert → Chart → Line Chart")
        print("4. Add 'ssthresh' as second series")
        print("5. Add 'rwnd' as third series")
        print("\nChart Settings:")
        print("  X-axis: Time (seconds)")
        print("  Y-axis: Window Size (packets)")
        print("  Title: 'Congestion Window Evolution Over Time'")
        print("  Legend: CWND, SSTHRESH, RWND")
        
        print("\n🐍 PYTHON (matplotlib):")
        print("-"*70)
        print("""
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('cwnd_data.csv')

# Create plot
plt.figure(figsize=(12, 6))
plt.plot(df['time'], df['cwnd'], label='CWND', linewidth=2)
plt.plot(df['time'], df['ssthresh'], label='SSTHRESH', linestyle='--', linewidth=2)
plt.plot(df['time'], df['rwnd'], label='RWND', linestyle=':', linewidth=2)

plt.xlabel('Time (seconds)', fontsize=12)
plt.ylabel('Window Size (packets)', fontsize=12)
plt.title('Congestion Window Evolution (30% Packet Loss)', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('cwnd_graph.png', dpi=300)
plt.show()
        """)
        
        print("\n📈 WHAT TO LOOK FOR IN GRAPH:")
        print("-"*70)
        print("✓ Slow Start: CWND grows exponentially (steep curve) until SSTHRESH")
        print("✓ Congestion Avoidance: CWND grows linearly after SSTHRESH")
        print("✓ Timeout Events: CWND drops to 1 (vertical drop)")
        print("✓ Fast Recovery: CWND drops to SSTHRESH/2 (partial drop)")
        print("✓ RWND Constraint: CWND may be limited by RWND values")
        print("✓ Sawtooth Pattern: Typical TCP behavior with growth and drops")
        
        print("\n💡 INTERPRETATION:")
        print("-"*70)
        print("• Rising CWND = Network has capacity, sender increases rate")
        print("• CWND drops = Packet loss detected (timeout or dup ACKs)")
        print("• CWND ≈ SSTHRESH = Transition from slow start to congestion avoidance")
        print("• CWND ≤ RWND = Flow control limiting send rate")
        print("="*70)


def main():
    """Main function to run data collection"""
    print("\n" + "="*70)
    print("CWND vs TIME DATA COLLECTOR")
    print("="*70)
    print("\nThis script will:")
    print("  1. Connect to receiver")
    print("  2. Send packets while collecting CWND/SSTHRESH/RWND data")
    print("  3. Export data to CSV file for graphing")
    print("  4. Generate test summary with parameters")
    print("\nMAKE SURE RECEIVER IS RUNNING FIRST!")
    print("  Terminal 1: python receiver_test.py")
    print("="*70)
    
    input("\nPress Enter when receiver is ready...")
    
    # Create collector
    collector = CWNDDataCollector()
    
    try:
        # Collect data
        collector.collect_transmission_data(
            num_packets=CONFIG['NUM_PACKETS'],
            packet_size=CONFIG['PACKET_SIZE']
        )
        
        # Export to CSV
        collector.export_to_csv('cwnd_data.csv')
        
        # Export summary
        collector.export_summary('test_summary.txt')
        
        # Print graphing instructions
        collector.print_graph_instructions()
        
        print("\n" + "="*70)
        print("✓✓✓ DATA COLLECTION COMPLETE ✓✓✓")
        print("="*70)
        print("\nFiles created:")
        print("  📄 cwnd_data.csv      - Data for graphing")
        print("  📄 test_summary.txt   - Test parameters and results")
        print("\nNext steps:")
        print("  1. Open cwnd_data.csv in Excel/Sheets")
        print("  2. Create line chart with time vs cwnd")
        print("  3. Include in your report as evidence of congestion control")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("Make sure receiver_test.py is running!")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
