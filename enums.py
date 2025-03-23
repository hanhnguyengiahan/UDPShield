from enum import Enum

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
