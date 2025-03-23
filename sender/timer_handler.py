import threading
from sender.sender import send_syn, send_fin
from helper import log_message, create_segment, SegmentType

def restart_timer(control, buffer, rto):
    """Restart the retransmission timer if needed."""
    if control.timer:
        control.timer.cancel()
    
    if any(buffer):  # If there are unACKed segments
        control.timer = threading.Timer(rto, timer_thread, args=(control, buffer, rto))
        control.timer.start()
    else:
        control.timer = None

def timer_thread(control, buffer, rto):
    """Handle retransmission on timeout."""
    print("Timeout occurred")

    if control.sending_segtype == SegmentType.SYN:
        log_message("sender", SegmentType.SYN, control.recv_seqno, 0, "drp", control.start_time, False)
        send_syn(control, False)

    elif control.drop_fin:
        send_fin(control)
        control.drop_fin = False

    elif buffer[control.send_base]:
        segment = buffer[control.send_base]
        data_segment = create_segment(segment.segtype, segment.seqno, segment.data)
        log_message("sender", SegmentType.DATA, segment.seqno, len(segment.data), "s", control.start_time, False)
        control.socket.send(data_segment)

    control.lock.acquire()
    if control.timer:
        control.timer.cancel()
    control.timer = threading.Timer(rto, timer_thread, args=(control, buffer, rto))
    control.timer.start()
    control.dupACK_count = 0
    control.lock.release()
