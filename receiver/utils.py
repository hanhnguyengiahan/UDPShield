import sys
import time

def parse_port(port_str):
    try:
        port = int(port_str)
        if not (1024 <= port <= 65535):
            raise ValueError
        return port
    except ValueError:
        sys.exit("Error: Invalid port number. Must be between 1024 and 65535.")

def log_message(entity, segtype, seqno, length, action, start_time, is_first):
    timestamp = 0 if is_first else round(time.time() * 1000 - start_time, 2)
    with open("logs/receiver_log.txt", 'a') as log:
        log.write(f"{entity} {action} {segtype} {seqno} {length} {timestamp}\n")
