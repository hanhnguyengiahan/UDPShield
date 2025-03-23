import threading
import socket
from data_structures import Control, State, SegmentType
from utils import log_message, is_to_be_dropped
from segment_utils import create_segment
from timer_handler import restart_timer

class Sender:
    """Handles sending data, managing acknowledgments, and handling TCP-like states."""

    def __init__(self, control: Control, buffer, rto, max_win, rlp):
        self.control = control
        self.buffer = buffer
        self.rto = rto
        self.max_win = max_win
        self.rlp = rlp
        self.recv_thread = threading.Thread(target=self._recv_thread, daemon=True)
    
    def start(self):
        """Starts the sender process."""
        self.recv_thread.start()
    
    def _recv_thread(self):
        """Thread function to receive and process acknowledgments."""
        while self.control.is_alive:
            try:
                nread = self.control.socket.recv(4)
            except (BlockingIOError, ConnectionRefusedError):
                self.control.is_alive = False
                break

            segtype = int.from_bytes(nread[:2], "big")
            recv_seqno = int.from_bytes(nread[2:4], "big")

            with self.control.lock:
                log_message("sender", SegmentType(segtype), recv_seqno, 0, "rcv", self.control.start_time, False)

                if self.control.last_segment_seqno == recv_seqno:
                    self._handle_final_ack()

                elif self.control.sender_state == State.SYN_SENT:
                    self._handle_syn_ack(recv_seqno)

                elif self.control.sender_state == State.EST:
                    self._handle_established_ack(recv_seqno)

                elif self.control.sender_state == State.FIN_WAIT:
                    self._handle_fin_ack(recv_seqno)

    def _handle_final_ack(self):
        """Handles the final acknowledgment for closing the connection."""
        self.control.sender_state = State.CLOSING
        if self.control.timer:
            self.control.timer.cancel()
            self.control.timer = None

    def _handle_syn_ack(self, recv_seqno):
        """Handles the SYN-ACK response in the handshake process."""
        if is_to_be_dropped(self.rlp):
            self.control.recv_seqno = recv_seqno
            return
        self.control.sender_state = State.EST

    def _handle_established_ack(self, recv_seqno):
        """Handles acknowledgments during the established state."""
        index = next(
            (i for i, seg in enumerate(self.buffer) if seg and (seg.seqno + len(seg.data)) % 2**16 == recv_seqno),
            -1
        )

        if index == self.control.send_base and self.buffer[index]:
            self.buffer[index] = None
            self.control.send_base = (self.control.send_base + 1) % int(self.max_win / 1000)
            restart_timer(self.control, self.buffer, self.rto)
            self.control.dupACK_count = 0
        elif self.buffer[self.control.send_base] and self.buffer[self.control.send_base].seqno == recv_seqno:
            self.control.dupACK_count += 1
            if self.control.dupACK_count == 3:
                self._handle_triple_dup_ack(recv_seqno)

    def _handle_triple_dup_ack(self, recv_seqno):
        """Handles fast retransmission on triple duplicate ACKs."""
        data_segment = create_segment(SegmentType.DATA, recv_seqno, self.buffer[self.control.send_base].data)
        log_message("sender", SegmentType.DATA, recv_seqno, len(data_segment) - 4, "fst", self.control.start_time, False)
        self.control.socket.send(data_segment)
        self.control.dupACK_count = 0

    def _handle_fin_ack(self, recv_seqno):
        """Handles acknowledgment of FIN packet, completing the termination process."""
        self.control.is_alive = False
        self.control.sender_state = State.FINISHED
