import time
import random
 
def log_message(user, segtype, seqno, num_bytes, action, start_time, first):
    log_file = f"{user}_log.txt"
    with open(log_file, 'a') as file:
        timestamp = 0.00 if first else round(time.time() * 1000 - start_time, 2)
        file.write(f"{action:<3} {timestamp:<11} {segtype.name:<4} {seqno:<5} {num_bytes}\n")

def print_buffer(buffer):
    print(" ".join(str(seg.seqno) if seg else "None" for seg in buffer))

def find_expected_segno(max_win, receive_buffer, index, file_received):
    """Finds the expected sequence number and writes ordered data to file."""
    expected_seqno = None
    cur_index = (index + 1) % len(receive_buffer)
    
    while receive_buffer[cur_index]:
        with open(file_received, 'a') as f:
            f.write(receive_buffer[cur_index].data.decode('utf-8'))
        
        expected_seqno = (receive_buffer[cur_index].seqno + len(receive_buffer[cur_index].data)) % (2**16)
        print(f'write seqno: {receive_buffer[cur_index].seqno}')
        receive_buffer[cur_index] = None
        
        cur_index = (cur_index + 1) % len(receive_buffer)
    
    return expected_seqno, cur_index

def write_to_file(max_win, receive_buffer, file_received):
    """Writes buffered data to file sequentially."""
    for i in range(int(max_win / 1000)):
        if not receive_buffer[i]:
            break
        mode = 'w' if i == 0 else 'a'
        with open(file_received, mode) as file:
            file.write(chr(receive_buffer[i].data))

def should_drop_packet(probability):
    """Determines if a packet should be dropped based on probability."""
    return random.random() < probability

def clear_recv_buffer_if_full(buffer, max_win):
    """Clears the receive buffer if full."""
    if all(buffer[i] for i in range(int(max_win / 1000))):
        buffer[:] = [None] * len(buffer)
    return buffer
