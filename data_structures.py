from dataclasses import dataclass
import socket
import threading
from .enums import SegmentType, State

@dataclass
class SenderSegment:
    seqno: int
    segtype: SegmentType
    data: bytes

@dataclass
class ReceiverSegment:
    seqno: int
    segtype: SegmentType
    data: int

@dataclass
class Control:
    sender_port: int
    receiver_port: int
    socket: socket.socket
    run_time: int
    start_time: float
    timer: threading.Timer
    last_segment_seqno: int
    lock: threading.Lock
    isn: int
    recv_seqno: int
    dupACK_count: int = 0
    send_base: int = 0
    is_alive: bool = True
    sender_state: State = State.CLOSED
    drop_fin: bool = False
    drop_syn: bool = False
