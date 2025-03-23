import socket

def setup_socket(sender_port, receiver_port, timeout=None):
    """Set up a UDP socket with optional timeout."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', sender_port))
    sock.connect(('127.0.0.1', receiver_port))
    
    if timeout is None:
        sock.setblocking(True)
    else:
        sock.settimeout(timeout)
    
    return sock
