import struct
from enums import SegmentType

def create_segment(segtype, seqno, data):
    """Creates a segment with STP header and payload."""
    header = (segtype.value << 16 | seqno).to_bytes(4, "big")
    return header + (data.encode('utf-8') if isinstance(data, str) else data)

def unpack_segment(buffer):
    """Extracts segment type, sequence number, and data from a received buffer."""
    header = struct.unpack_from('>I', buffer, offset=0)[0]
    segtype = SegmentType((header >> 16) & 0xFFFF)
    seqno = header & 0xFFFF
    data = b'' if segtype in {SegmentType.SYN, SegmentType.FIN} else buffer[4:]
    return segtype, seqno, data