import struct

def create_segment(segtype, seqno, data):
    header = f"{segtype} {seqno} ".encode()
    return header + data.encode()

def unpack_segment(segment):
    parts = segment.decode().split(" ", 2)
    segtype, seqno = parts[0], int(parts[1])
    data = parts[2] if len(parts) > 2 else ''
    return segtype, seqno, data
