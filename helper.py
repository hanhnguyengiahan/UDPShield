import time
from dataclasses import dataclass
from enum import Enum
import struct
import socket
import threading
import random
class SegmentType(Enum):
    DATA = 0
    ACK = 1
    SYN = 2
    FIN = 3

class State(Enum):
    CLOSED = 0
    LISTEN = 1
    SYN_SENT = 2
    EST = 3
    CLOSING = 4
    FIN_WAIT = 5
    TIME_WAIT = 6
    FINISHED = 7

@dataclass
class SenderSegment:
    """"Segment Data structure to store in sender buffer"""  
    seqno: int
    segtype: SegmentType
    data: bytes

@dataclass
class ReceiverSegment:
    """"Segment Data structure to store in receiver buffer"""  
    seqno: int
    segtype: SegmentType
    data: int

@dataclass
class Control:
    """Control block: parameters for the sender program."""
    sender_port: int        # Port number of the sender
    receiver_port: int   # Port number of the receiver
    socket: socket.socket   # Socket for sending/receiving messages
    run_time: int           # Run time in seconds
    start_time: float
    timer: threading.Timer
    last_segment_seqno: int
    lock: threading.Lock
    isn: int
    dupACK_count= 0
    send_base = 0
    is_alive: bool = True   # Flag to signal the sender program to terminate
    sender_state: State = State.CLOSED
    drop_fin: bool = False
    drop_syn: bool = False
    



def log_message(user, type, seqno, num_bytes, action, start_time, first):
    log_file = f"{user}_log.txt"
    with open(log_file, 'a') as file:
        if (first): 
            tim = 0.00
            file.write(f"{action:<3}     {tim:<11} {type.name:<4}   {seqno:<5} 0\n")
        else:
            timestamp = round(time.time()*1000 - start_time, 2)
            # print("timestamp:", timestamp)
            file.write(f"{action:<3}     {timestamp:<11} {type.name:<4}   {seqno:<5} {num_bytes}\n")
    
            
def print_buff(buffer):
    for segment in buffer:
        if segment == None: print('None ', end='')
        else: print(segment.seqno, end=' ')
    print()

def create_segment(segtype, seqno, data):
    segtype_bytes = segtype.value.to_bytes(2, "big")

    seqno = seqno.to_bytes(2, "big")

    header = segtype_bytes + seqno
    
    header_int = int.from_bytes(header, "big")
    
    stp_header = struct.pack('>I', header_int)  

    # segment = stp_header + data.encode('utf-8')
    if type(data) is str: data = data.encode('utf-8')

    segment = stp_header + data

    return segment

def unpack_segment(buffer):
    header = struct.unpack_from('>I', buffer, offset=0)[0]
    segtype = SegmentType((header >> 16) & 0xFFFF)
    seqno = header & 0xFFFF
    if (segtype == SegmentType.SYN or segtype == SegmentType.FIN): data = ''
    else: data = buffer[4:]
    return segtype,seqno, data


def find_expected_segno(max_win, receive_buffer, index, buf, file_received):
    expected_seqno = None
    # f.write(str(receive_buffer[index].data, encoding='utf-8'))

    cur_index = (index + 1) % len(receive_buffer)
    # f = open(file_received, 'a') 
    while True:
        current = receive_buffer[cur_index]
        if current is None:
            # f.write()
            return expected_seqno, cur_index
        else:
            f = open(file_received, 'a') 
            f.write(str(receive_buffer[cur_index].data, encoding='utf-8'))
            f.close()
            expected_seqno = (current.seqno + len(receive_buffer[cur_index].data)) % (2**16)
            # print(f"cur index: {cur_index}, len: {len(receive_buffer[cur_index].data)}")
            print(f'write seqno: {current.seqno}')
            receive_buffer[cur_index] = None
            
        cur_index += 1
        if cur_index == len(receive_buffer):
            cur_index = 0
    # f.close()
        
def write_to_file(max_win, receive_buffer, file_received):
    for i in range(0, int(max_win / 1000)):
        if not receive_buffer[i]:
            break
        else:
            if (i == 0):
                with open(file_received, 'w') as file:
                    file.write(chr(receive_buffer[i].data))
            else:
                with open(file_received, 'a') as file:
                    file.write(chr(receive_buffer[i].data))
            return file

def is_to_be_dropped(probability):
    # random.seed(1)
    random_value = random.random()
    if (random_value < probability):
        return True
    else:
        return False
    
def remove_all_in_recv_buffer_if_full(buffer, max_win):
    flag = True
    for i in range(0, int(max_win / 1000)):
        if buffer[i] == None:
            flag = False
            break
        else: continue
    if (flag == True):
        for i in range(0, int(max_win / 1000)):
            buffer[i] = None
    return buffer