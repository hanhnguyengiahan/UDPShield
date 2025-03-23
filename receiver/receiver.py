import socket
import time
from receiver.segment_utils import unpack_segment, create_segment
from buffer import ReceiverBuffer
from utils import log_message
from constants import BUF_SIZE, MSS, SegmentType

class Receiver:
    def __init__(self, receiver_port, sender_port, file_received, max_win):
        self.receiver_port = receiver_port
        self.sender_port = sender_port
        self.file_received = file_received
        self.max_win = max_win
        self.start_time = 0.0
        self.expected_seqno = -1
        self.buffer = ReceiverBuffer(max_win, MSS)
    
    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('127.0.0.1', self.receiver_port)) 
            s.connect(('127.0.0.1', self.sender_port))
            
            open("logs/receiver_log.txt", 'w').close()
            open(f"received_files/{self.file_received}", 'w').close()
            
            while True:
                buf = s.recv(BUF_SIZE)
                segtype, seqno, data = unpack_segment(buf)
                if segtype != SegmentType.SYN:
                    log_message("receiver", segtype, seqno, MSS, "rcv", self.start_time, False)
                
                if segtype == SegmentType.SYN:
                    self.handle_syn(s, seqno)
                elif segtype == SegmentType.DATA:
                    self.handle_data(s, seqno, data)
                elif segtype == SegmentType.FIN:
                    self.handle_fin(s, seqno)
                    break
    
    def handle_syn(self, s, seqno):
        self.expected_seqno = seqno + 1
        log_message("receiver", SegmentType.SYN, seqno, MSS, "rcv", 0.00, True)
        ack_segment = create_segment(SegmentType.ACK, seqno + 1, '')
        self.start_time = time.time() * 1000
        log_message("receiver", SegmentType.ACK, seqno + 1, 0, "snd", self.start_time, False)
        s.send(ack_segment)
    
    def handle_data(self, s, seqno, data):
        ack_seqno = self.buffer.process_data(seqno, data, self.file_received)
        log_message("receiver", SegmentType.ACK, ack_seqno, 0, "snd", self.start_time, False)
        ack_segment = create_segment(SegmentType.ACK, ack_seqno, '')
        s.send(ack_segment)
    
    def handle_fin(self, s, seqno):
        log_message("receiver", SegmentType.ACK, seqno + 1, MSS, "snd", self.start_time, False)
        fin_ack = create_segment(SegmentType.ACK, seqno + 1, '')
        s.send(fin_ack)
        time.sleep(2)
