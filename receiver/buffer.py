class ReceiverBuffer:
    def __init__(self, max_win, mss):
        self.buffer = {}
        self.max_win = max_win
        self.mss = mss
        self.expected_seqno = -1

    def process_data(self, seqno, data, file_received):
        if seqno in self.buffer or seqno < self.expected_seqno:
            return self.expected_seqno
        
        self.buffer[seqno] = data
        
        while self.expected_seqno in self.buffer:
            with open(f"received_files/{file_received}", 'a') as f:
                f.write(self.buffer[self.expected_seqno])
            del self.buffer[self.expected_seqno]
            self.expected_seqno += len(data)
        
        return self.expected_seqno
