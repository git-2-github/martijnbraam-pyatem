The USB protocol
================

The ATEM Mini series of switchers can be controlled over USB instead of ethernet. This variant of the protocol is a
simplified version of the UDP protocol used for the other ATEM hardware.

The USB protocol drops all the retransmission and framing from the UDP protocol since USB is a reliable transport and
provides framing already.

The old USB protocol (until 8.5)
--------------------------------

The initial revision of the USB protocol is very simple. The raw ATEM commands are just send over a bulk endpoint
prefixed with the length of a block of commands.

The ATEM hardware uses a standard pair of bulk endpoints for all the communication except the initial handshake.

The interfaces exposed by an ATEM Mini:

=========  ================  =====
Interface  Class             Notes
=========  ================  =====
0          Vendor specific   Unknown
1          Vendor specific   Unknown
2          Vendor specific   ATEM control protocol
3          DFU               Firmware updates
4          Video  control    Virtual webcam settings
5          Video  stream     Virtual webcam stream
6          Audio control     Virtual soundcard settings
7          Audio stream      Virtual soundcard stream
=========  ================  =====


Starting a connection
^^^^^^^^^^^^^^^^^^^^^

The communication is established by sending a vendor USB control transfer to the device and then atem commands are sent
using regular bulk packets. The ATEM protocol is on interface 2.

+---------------+------------------+----------------------------------+
| Type          | Control Transfer |                                  |
+---------------+------------------+----------------------------------+
| bmRequestType | 0x21             | host-to-device, class, interface |
+---------------+------------------+----------------------------------+
| bRequest      | 0                |                                  |
+---------------+------------------+----------------------------------+
| wValue        | 0x0000           |                                  |
+---------------+------------------+----------------------------------+
| wIndex        | 0x0002           |                                  |
+---------------+------------------+----------------------------------+
| wLength       | 0                |                                  |
+---------------+------------------+----------------------------------+

After this initial packet it should be possible to do an URB Bulk read to get the full initial sync in one packet.

The pyatem implementation does reads with a size of 32768 bytes.

Packet protocol
^^^^^^^^^^^^^^^

The USB protocol is simplified a lot compared to the older UDP protocol. Since USB already provides a robust, ordered
and framed protocol a lot of the error recovery features could be dropped.

======  ======  =====
Offset  Length  Note
======  ======  =====
0       4       Chunk length as int32 (n after this)
4       n       Atem messages concatinated together
4+n     4       (optional) Chunk length of the second chunk. These chunks and data blocks repeat
======  ======  =====

The contents of the ATEM messages are what's defined as :ref:`high-level-protocol` on the UDP page. All further parsing
is exactly the same as the UDP protocl.

For sending commands to the ATEM the inverse can be done. Prepend a 32 bit length header to the normal ATEM command
structure and write it as an USB Bulk message


The 8.6+ protocol
-----------------

With the introduction of the ATEM Mini Extreme the protocol got revised for all Mini series switchers. There is no
longer a control transfer to start the connection and there's an additional header to implement some flow control
and the initial handshake. The 4-byte packet length prefix from the previous protocol has been completely dropped.

Starting a connection
^^^^^^^^^^^^^^^^^^^^^

The connection only uses the bulk transfer endpoints on interface 2. The new header for the protocol uses 4 bytes and
up to 8 bytes of extra payload.

======  ======  =====
Offset  Length  Note
======  ======  =====
0       1       The packet type for ATEM -> PC packets, otherwise 0
1       1       The packet type for PC -> ATEM packets, otherwise 0
2       1       Unknown, 1 for ATEM -> PC packets, 0 otherwise
3       1       Unknown, 1 for PC -> ATEM transfers, 0 otherwise
4       0-8     Data. Depends on packet type
======  ======  =====

The important data that's encoded here is the packet type. The packet types are the following:

+--------+-------------------------+--------------------------------------------------+
| Type   | Data                    | Description                                      |
+========+=========================+==================================================+
| 0x01   | 00 01 10 92             | Send from PC -> ATEM to start a new connection.  |
+--------+-------------------------+--------------------------------------------------+
| 0x02   | no data                 | Send from ATEM -> to acknowledge the init packet |
+--------+-------------------------+--------------------------------------------------+
| 0x03   | 00 00 00 00 00 00 xx xx | Send from PC -> ATEM to signify RX buffer usage  |
+        +-------------------------+--------------------------------------------------+
| 0x03   | xx xx 00 00 00 00 00 00 | Send from ATEM -> PC to signify RX buffer usage  |
+--------+-------------------------+--------------------------------------------------+
| 0x04   | 00 00 00 00 00 00 xx xx | The next packet is PC -> ATEM data               |
+        +-------------------------+--------------------------------------------------+
| 0x04   | 00 00 00 00 00 00 xx xx | The next packet is ATEM -> PC data               |
+--------+-------------------------+--------------------------------------------------+
| 0x05   | no data                 | Send from PC -> ATEM                             |
+--------+-------------------------+--------------------------------------------------+

The meaning of the 4 bytes in the 0x01 packet are still unknown.

The 0x03 packets are used for some variant of flow control between the devices. The
buffer usage is described as blocks of 1024 bytes. If floor(len(buffer) // 1024) becomes
more than 0 then a packet with that value are sent to signify the other end to start
slowing down.

The 0x04 packets are the main packets of the protocol. This packet just signifies that
the _next_ USB packet(s) are ATEM protocol buffers. The encoding for these buffers is
the same as the old protocol except there's no length prefix for the packet. The packet
is simply the result of concatinating together encoded ATEM fields and commands. and
are decoded using the overall packet length in this new header and the command/field
size stored inside every command after the 4-byte command identifier.