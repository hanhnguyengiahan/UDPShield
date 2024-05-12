 UDPShield


  Overview
  --------

  
  Description
  -----------
  
  
  Features
  --------
  
  - Parsing command-line arguments
  - Communication via UDP sockets
  - Using a "connected" UDP socket, to send() and recv()
  - Conversion between host byte order and network byte order for 
    multi-byte fields.
  - Timers (sender only)
  - Multi-threading (sender only)
  - Simple logging
  
  
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
  
