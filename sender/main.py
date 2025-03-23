import socket
import threading
from sender import Sender
from data_structures import Control

if __name__ == "__main__":
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_socket.setblocking(False)
    
    control = Control(
        sender_port=5000,
        receiver_port=6000,
        socket=sender_socket,
        run_time=60,
        start_time=0,
        timer=None,
        last_segment_seqno=0,
        lock=threading.Lock(),
        isn=0,
        recv_seqno=0
    )

    buffer = [None] * 10
    rto = 1.0
    max_win = 10240
    rlp = 0.1

    sender = Sender(control, buffer, rto, max_win, rlp)
    sender.start()
