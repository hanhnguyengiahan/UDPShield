#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import socket
import sys
import threading
import time
from helper import Control, SegmentType, State, log_message, create_segment, SenderSegment, is_to_be_dropped, print_buff
# generate random integer values
from numpy.random import seed
from numpy.random import randint
import array as arr

NUM_ARGS  = 7  # Number of command-line arguments
BUF_SIZE  = 4  # Size of buffer for receiving messages
MAX_SLEEP = 2  # Max seconds to sleep before sending the next message
MSS = 1000

segno = -1

def parse_run_time(run_time_str, min_run_time=1, max_run_time=60):
    """Parse the run_time argument from the command-line.

    The parse_run_time() function will attempt to parse the run_time argument
    from the command-line into an integer. If the run_time argument is not 
    numerical, or within the range of acceptable run times, the program will
    terminate with an error message.

    Args:
        run_time_str (str): The run_time argument from the command-line.
        min_run_time (int, optional): Minimum acceptable run time. Defaults to 1.
        max_run_time (int, optional): Maximum acceptable run time. Defaults to 60.

    Returns:
        int: The run_time as an integer.
    """
    try:
        run_time = float(run_time_str) / 1000.0
    except ValueError:
        sys.exit(f"Invalid run_time argument, must be numerical: {run_time_str}")
    
                 
    return run_time

def parse_port(port_str, min_port=49152, max_port=65535):
    try:
        port = int(port_str)
    except ValueError:
        sys.exit(f"Invalid port argument, must be numerical: {port_str}")
    
    if not (min_port <= port <= max_port):
        sys.exit(f"Invalid port argument, must be between {min_port} and {max_port}: {port}")
                 
    return port

def setup_socket(sender_port, receiver_port,timeout=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # bind to sender port
    sock.bind(('127.0.0.1', sender_port))
    # connect to peer's address
    sock.connect(('127.0.0.1', receiver_port))
    # print(timeout)
    if timeout is None:
        sock.setblocking(True)
    else:
        sock.settimeout(timeout)
    return sock

def restart_timer(control, buffer, rto):
    # if there are currently any unACKed segments
    has_unACKed_segments = find_current_unACKed_segments(buffer)
    print("has unacked sm: ", has_unACKed_segments)

    if control.timer: control.timer.cancel()
    if (has_unACKed_segments):
        # restart timer
        control.timer = threading.Timer(rto, timer_thread, args=(control, buffer, rto))
        control.timer.start()

    # otherwise (there are no unACKed segments)
    else:
        # stop timer
        control.timer = None
        print('STOP timer: ')

def recv_thread(control, buffer, rto, max_win, rlp):
    global seqno
    global sending_segtype
    while control.is_alive:
        try:
            nread = control.socket.recv(BUF_SIZE)
        except BlockingIOError:
            continue    # No data available to read
        except ConnectionRefusedError:
            print(f"recv: connection refused by {control.sender_port}:{control.receiver_port}, shutting down...", file=sys.stderr)
            control.is_alive = False
            break
        
        segtype = int.from_bytes(nread[:2], "big")
        recv_seqno = int.from_bytes(nread[2:4], "big")
        print("recv_seqno", recv_seqno)
        print("current state: ", control.sender_state)
        control.lock.acquire()
        
        if control.last_segment_seqno == recv_seqno:
            log_message("sender", SegmentType(segtype), recv_seqno, 0, "rcv", control.start_time, False)
            control.sender_state = State.CLOSING
            
            if control.timer:
                control.timer.cancel()
                control.timer = None

        # Update sender state based on segment type
        if control.sender_state == State.SYN_SENT:
            print("hiiiiii")
            # fixxxxxxxxxxx later to drop rlp
            if sending_segtype == SegmentType.SYN:
                print("drop syn-ack")
                log_message("sender", SegmentType(segtype), recv_seqno, 0, "drp", control.start_time, False)
                # fix later
                sending_segtype = SegmentType.DATA
                control.lock.release()
                continue
            log_message("sender", SegmentType(segtype), recv_seqno, 0, "rcv", control.start_time, False)
            
            control.sender_state = State.EST
            seqno += 1
            
        elif control.sender_state == State.EST:
            index = -1
            for i in range(0, len(buffer)):
                if buffer[i] and (buffer[i].seqno + len(buffer[i].data)) % 2**16 == recv_seqno:
                    index = i
                    break
            
            # if (is_to_be_dropped(rlp)):
            #     log_message("sender", SegmentType(segtype), recv_seqno, 0, "drp", control.start_time, False)
            #     continue
            
            log_message("sender", SegmentType(segtype), recv_seqno, 0, "rcv", control.start_time, False)
            print("buffer bf: ", end='')
            print_buff(buffer)
            
            print("control.send_base: ", control.send_base)
            print("recv_seqno received: ", recv_seqno)
            # if ACK acknowledges previously unACKed segment(s)
            if (index == control.send_base and buffer[index] != None):
               
                buffer[index] = None
               
                control.send_base = (control.send_base + 1) % int(max_win / MSS)
              
                 
                restart_timer(control, buffer, rto)

                
                control.dupACK_count = 0
                
            # otherwise (ACK acknowledges previously ACKed segments)
            elif buffer[control.send_base] and buffer[control.send_base].seqno == recv_seqno:
                # increment dupACKcoun
                control.dupACK_count += 1
                print(f'dupACKcount: {control.dupACK_count}')
                if (control.dupACK_count == 3):
                    data_segment = create_segment(SegmentType(segtype), recv_seqno, buffer[control.send_base].data)
                    log_message("sender", SegmentType(segtype), seqno, int(len(data_segment)) - 4, "fst", control.start_time, False)

                    control.socket.send(data_segment)

                    control.dupACK_count = 0      
            
                                                                                                             
            elif index != control.send_base: 
                print("index > sb", index, control.send_base)
                if control.timer:
                    control.timer.cancel()
                    control.timer = None
                
                while index != control.send_base:
                    buffer[control.send_base] = None
                    control.send_base = (control.send_base + 1) % int(max_win / MSS)
                buffer[control.send_base] = None
                control.send_base = (control.send_base + 1) % int(max_win / MSS)

                restart_timer(control, buffer, rto)


        elif control.sender_state == State.FIN_WAIT:
            print("seqtype (should be ACK for fin segment): ", segtype)
            log_message("sender", SegmentType(segtype), recv_seqno, 0, "rcv", control.start_time, False)
            print("after log for fin ack")
            control.is_alive = False
            control.sender_state = State.FINISHED
        # Log the received message
        print(f"recv_seqno received: {recv_seqno}, rcv: {segtype}")
        print("bufer after: ", end='')
        print_buff(buffer)
        control.lock.release()         
def find_current_unACKed_segments(buffer):
    
    for i in range(0, len(buffer)):
        if buffer[i]:
            return True
    return False
def timer_thread(control, buffer, rto):
    
    """Stop execution when the timer expires.

    The timer_thread() function will be called when the timer expires. It will
    print a message to the log, and set the `is_alive` flag to False. This will
    signal the receiver thread, and the sender program, to terminate.

    Args:
        control (Control): The control block for the sender program.
    """
   
    
    print("timeout")
    

    global seqno
    global sending_segtype
    if sending_segtype == SegmentType.SYN:
        print("timeout retransmit a syn")
        send_syn(control, False)

    elif (control.drop_fin):
        send_fin(control)
        control.drop_fin = False

    elif buffer[control.send_base]:
        i = control.send_base
        print("index to resend(shud be 0): ", i)
        data_segment = create_segment(buffer[i].segtype, buffer[i].seqno, buffer[i].data)
        print("len data retransmit: ", len(buffer[i].data))
        log_message("sender", SegmentType.DATA, buffer[i].seqno, len(buffer[i].data), "s", control.start_time, False)
        control.socket.send(data_segment)
        print("we shud resend data segment now")
        
        
    else: 
        print("nothing happen in timeout")
        return
    
    # restart timer
    control.lock.acquire()
    print("has taken the lock in timeout")

    if control.timer: control.timer.cancel()
    control.timer = threading.Timer(rto, timer_thread, args=(control, buffer, rto))
    control.timer.start()

    # reset dupACKcount
    control.dupACK_count = 0

    control.lock.release()
    print("has released")
    
     
def send_syn(control, is_first):
    global seqno
    segtype = SegmentType.SYN
    syn_segment = create_segment(segtype, seqno, "")
    if (is_first):
        control.start_time = time.time()*1000
        control.sender_state = State.SYN_SENT
        
        log_message("sender", segtype, seqno, 0, "snd", 0.00, True)
           
        segment_sent = control.socket.send(syn_segment)

    else: 
        print("retransmit a syn")
        control.sender_state = State.SYN_SENT
        log_message("sender", segtype, seqno, 0, "snd", control.start_time, False)
        segment_sent = control.socket.send(syn_segment)
        
    
def send_data(flp, control, num_times_to_send, file, buffer):
    global seqno
   

    if file.closed == True:
        return
    
    is_eof = False
    control.lock.acquire()
    i = control.send_base
    control.lock.release()

    for _ in range(0, num_times_to_send):
        if is_eof: break

        # if the buffer[i] is None, we send the data
        if buffer[i] == None:
            data_to_send = file.read(MSS)
            
            # if the seqno exceeds 2^16 - 1, we cycle it back to zero
        

            control.lock.acquire()
            
            if not control.timer:
                control.timer = threading.Timer(rto, timer_thread, args=(control, buffer, rto))
                control.timer.start()
            control.lock.release()
            
            segtype = SegmentType.DATA
                        

            syn_segment = create_segment(segtype, seqno, data_to_send)
            buffer[i] = SenderSegment(seqno, segtype, data_to_send)

        
            
            # if we reach the end of the file, we moves to CLOSING state and stop sending data
            next_data = file.read(1)
            if not next_data:
                control.last_segment_seqno = (seqno + len(data_to_send)) % (2**16)
                file.close()
                is_eof = True
            # goes back 1 byte after reading 1
            if not (file.closed):
                file.seek(-1, 1)

            if (is_to_be_dropped(flp)):
                log_message("sender", segtype, seqno, int(len(data_to_send)), "drp", control.start_time, False)

            else: 
                log_message("sender", segtype, seqno, int(len(data_to_send)), "snd", control.start_time, False)
                control.socket.send(syn_segment)
            if (seqno + len(data_to_send)) > 2**16 - 1:
                control.isn = control.isn - (2**16)
            seqno = (seqno + len(data_to_send)) % (2**16)
        i = (i + 1) % len(buffer)


def send_fin(control):
    global seqno
    segtype = SegmentType.FIN
    control.lock.acquire()

    if (control.drop_fin):
        if control.timer:
            control.timer.cancel()
            control.timer = None

        log_message("sender", segtype, seqno, 0, "drp", control.start_time, False)

    else:
        fin_segment = create_segment(segtype, seqno, "")
        log_message("sender", segtype, seqno, 0, "snd", control.start_time, False)
        segment_sent = control.socket.send(fin_segment)
        control.sender_state = State.FIN_WAIT
    
    control.lock.release()


if __name__ == "__main__":
    if len(sys.argv) != NUM_ARGS + 1:
        sys.exit(f"Usage: {sys.argv[0]} sender_port receiver_port txt_file_to_send max_win rto flp rlp ")
   
    sender_port = parse_port(sys.argv[1])
    
    receiver_port = parse_port(sys.argv[2])
    file_to_send = sys.argv[3]
    # empty log file
    with open("sender_log.txt", 'w') as f:
        pass

    max_win = int(sys.argv[4])
    rto = parse_run_time(sys.argv[5])
    flp = float(sys.argv[6])
    rlp = float(sys.argv[7])


    # declare a buffer where each element has type of Segment 
    buffer = [None] * int(max_win / MSS)
   
    # declare an index to keep track of buffer

    sock = setup_socket(sender_port, receiver_port)
    lock = threading.Lock() 
    isn = 23
    global seqno
    global sending_segtype

    sending_segtype = SegmentType.SYN
    seqno = isn
    # Create a control block for the sender program.
    control = Control(sender_port, receiver_port, sock, rto, 0.00, None, -1, lock, isn)
    
    control.timer = threading.Timer(rto, timer_thread, args=(control, buffer, rto))
    
    # isn = random.randrange(2**16)
    
    # Start the receiver and timer threads.
    receiver = threading.Thread(target=recv_thread, args=(control, buffer, rto, max_win, rlp))
    receiver.start()
    
    if (is_to_be_dropped(flp)):
        log_message("sender", sending_segtype, seqno, 0, "drp", 0.00, True)
    

    control.timer.start()

    random.seed()  # Seed the random number generator
    

    # at the beginning, the state is CLOSED since we have not yet sent a SYN
    control.sender_state = State.CLOSED
    
    data_to_drop = []
   

    is_first = True
    while control.sender_state == State.CLOSED:
        send_syn(control, is_first)
        is_first = False

    while control.sender_state != State.EST:
        pass
    # segtype = SegmentType.DATA
    num_times_to_send = int(max_win / MSS)
    file = open(file_to_send, 'rb')
    y = 0
    while control.sender_state == State.EST: 
        if (control.sender_state == State.CLOSING):
            break
        send_data(flp, control, num_times_to_send, file, buffer)
        y += 1

    while control.sender_state != State.CLOSING:
        pass
    
    while control.sender_state == State.CLOSING:
        if (is_to_be_dropped(flp)):
            control.drop_fin = True
        else: control.drop_fin = False
        send_fin(control)


    while control.sender_state == State.FIN_WAIT:
        pass
    
    
    if (control.sender_state == State.FINISHED):

        receiver.join()
        if control.timer:
            control.timer.cancel()

        control.socket.close()  # Close the socket
        f.close()
        print("Shut down complete.")

        sys.exit(0)
    