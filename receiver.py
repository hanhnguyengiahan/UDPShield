#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###
# Main Modifications
# ==================
# Command line arguments: now include my_port, peer_port (the other side's port).
# Bind and connect: use bind((('127.0.0.1', my_port)) to bind to own port and connect(('127.0.0.1', peer_port)) to a specific sender.
# Data Receiving and Sending: Receive data via recv() and send a response using send() without specifying the other party's address and port.
# Changes to the log output.
###

import socket
import sys
from enum import Enum
import struct
from UDPShield.helper import print_buff, Control, SegmentType, State, log_message, create_segment, unpack_segment, ReceiverSegment, find_expected_segno, write_to_file, remove_all_in_recv_buffer_if_full
import time

NUM_ARGS = 4  # Number of command-line arguments
BUF_SIZE = 1024  # Size of buffer for sending/receiving data
MSS = 1000

def parse_wait_time(wait_time_str, min_wait_time=1, max_wait_time=60):
    """Parse the wait_time argument from the command-line.

    The parse_wait_time() function will attempt to parse the wait_time argument
    from the command-line into an integer. If the wait_time argument is not 
    numerical, or within the range of acceptable wait times, the program will
    terminate with an error message.

    Args:
        wait_time_str (str): The wait_time argument from the command-line.
        min_wait_time (int, optional): Minimum acceptable wait time. Defaults to 1.
        max_wait_time (int, optional): Maximum acceptable wait time. Defaults to 60.

    Returns:
        int: The wait_time as an integer.
    """
    try:
        wait_time = int(wait_time_str)
    except ValueError:
        sys.exit(f"Invalid wait_time argument, must be numerical: {wait_time_str}")
    
    if not (min_wait_time <= wait_time <= max_wait_time):
        sys.exit(f"Invalid wait_time argument, must be between {min_wait_time} and {max_wait_time} seconds: {wait_time_str}")
                 
    return wait_time

def parse_port(port_str, min_port=49152, max_port=65535):
    """Parse the port argument from the command-line.

    The parse_port() function will attempt to parse the port argument
    from the command-line into an integer. If the port argument is not 
    numerical, or within the acceptable port number range, the program will
    terminate with an error message.

    Args:
        port_str (str): The port argument from the command-line.
        min_port (int, optional): Minimum acceptable port. Defaults to 49152.
        max_port (int, optional): Maximum acceptable port. Defaults to 65535.

    Returns:
        int: The port as an integer.
    """
    try:
        port = int(port_str)
    except ValueError:
        sys.exit(f"Invalid port argument, must be numerical: {port_str}")
    
    if not (min_port <= port <= max_port):
        sys.exit(f"Invalid port argument, must be between {min_port} and {max_port}: {port}")
                 
    return port

if __name__ == "__main__":
    if len(sys.argv) != NUM_ARGS + 1:
        sys.exit(f"Usage: {sys.argv[0]} receiver_port sender_port txt_file_received max_win")


    receiver_port = parse_port(sys.argv[1])
    sender_port   = parse_port(sys.argv[2]) 
    file_received = str(sys.argv[3])
    max_win = int(sys.argv[4])
    start_time = 0.0
    first_time = True
    receive_buffer = [None] * int(max_win / MSS)
    expected_index = 0
    expected_seqno = -1
    index = -1
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('127.0.0.1', receiver_port)) 
        s.connect(('127.0.0.1', sender_port))
        with open("receiver_log.txt", 'w') as f:
            pass
        with open(file_received, 'w') as file:
            pass
        while True:
            buf = s.recv(BUF_SIZE)
            
                   
            segtype, seqno, data = unpack_segment(buf)
            if (segtype != SegmentType.SYN):
                log_message("receiver", segtype, seqno, MSS, "rcv", start_time, False)  
            
            if segtype == SegmentType.SYN:
                expected_seqno = seqno + 1
                isn = expected_seqno
                log_message("receiver", segtype, seqno, MSS, "rcv", 0.00, True)  
                segment = create_segment(SegmentType.ACK, seqno + 1, '')
                start_time = time.time()*1000
                log_message("receiver", SegmentType.ACK, seqno + 1, 0, "snd", start_time, False)
                segment_sent = s.send(segment)
                if (segment_sent != len(buf)):
                    print(f"sendto: partial/failed send, message: {buf}", file=sys.stderr)
                    continue
                
            if segtype == SegmentType.DATA:
                
                # if we haven't received the right packet, we buffer the receving one, and send the previous ACK again
                if (seqno != expected_seqno):
                    diff_seqno = (seqno - expected_seqno)
                    if diff_seqno < 0: diff_seqno += 2**16
                    index_offset = diff_seqno // 1000
                    final_index = (expected_index + index_offset) % int(max_win / MSS)

                    # buffer the receiving one
                    receive_buffer[final_index] = ReceiverSegment(seqno, segtype, data)
                    # send back the previous ack
                    log_message("receiver", SegmentType.ACK, expected_seqno, 0, "snd", start_time, False)
                    segment = create_segment(SegmentType.ACK, expected_seqno, '')
                    segment_sent = s.send(segment)
                else:
                    file = open(file_received, 'a')
                    file.write(str(data, encoding='utf-8'))
                    file.close()
                    receive_buffer[index] = None
                    expected_seqno, expected_index = find_expected_segno(max_win, receive_buffer, expected_index, buf, file_received)
                    if (expected_seqno == None):
                        expected_seqno = (seqno + len(buf) - 4) % (2**16)
                    
                
                    log_message("receiver", SegmentType.ACK, (seqno + len(buf) - 4) % (2**16), 0, "snd", start_time, False)
                    segment = create_segment(SegmentType.ACK, expected_seqno, '')

                    segment_sent = s.send(segment)
               
            if segtype == SegmentType.FIN:
            #    close the file
                
                log_message("receiver", SegmentType.ACK, seqno + 1, MSS, "snd", start_time, False)
                segment = create_segment(SegmentType.ACK, seqno + 1, '')
                segment_sent = s.send(segment)
                time.sleep(2)
                break
    f.close()
    sys.exit(0)

    