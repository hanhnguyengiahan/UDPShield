import sys
from receiver import Receiver
from utils import parse_port

if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(f"Usage: {sys.argv[0]} receiver_port sender_port txt_file_received max_win")
    
    receiver_port = parse_port(sys.argv[1])
    sender_port = parse_port(sys.argv[2])
    file_received = sys.argv[3]
    max_win = int(sys.argv[4])
    
    receiver = Receiver(receiver_port, sender_port, file_received, max_win)
    receiver.start()
