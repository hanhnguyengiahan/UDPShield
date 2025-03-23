 UDPShield


  Overview
  --------
 This project involves implementing a reliable transport protocol (STP) over UDP, mimicking key TCP features such as sequence numbers, acknowledgments (ACKs), timeouts, and sliding window protocol. Unlike TCP, UDP is unreliable, so STP ensures end-to-end reliable data transfer despite packet loss.
  
  Description
  -----------
  
  
  Features
  --------
  
  Asymmetric communication:

    - Sender → Receiver: Transmits data packets.
    
    - Receiver → Sender: Sends ACKs for received packets.

  Reliable Data Transfer:
  
    - Sliding window protocol (combining Go-Back-N & Selective Repeat).
  
    - Retransmissions using timeouts & duplicate ACKs.
  
    - Connection handling (SYN for setup, FIN for teardown).
  
    - Packet loss simulation to test reliability.
  
  
  Usage
  -----
  1. Run the sender program:
  
      $ python3 sender.py sender_port receiver_port txt_file_to_send max_win rto flp rlp
  
     This will invoke the sender to send a SYN segment to establish a 2-way-connection to
     the receiver at 127.0.0.1:[specified port], without limit time to terminate.
  

  2. Run the receiver program:
  
      $ python3 receiver.py receiver_port sender_port txt_file_received max_win
  
     This will invoke the receiver to listen on the specified port, and will terminate after 2 seconds.
  
  
  Notes
  -----
  
  - The sender and receiver are designed to be run on the same machine, 
    or on different machines on the same network. They are not designed 
    to be run on different networks, or on the public internet.
  
