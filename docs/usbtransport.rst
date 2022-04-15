The USB protocol
================

The ATEM Mini series of switchers can be controlled over USB instead of ethernet. This variant of the protocol is a
simplified version of the UDP protocol used for the other ATEM hardware.

The USB protocol drops all the retransmission and framing from the UDP protocol since USB is a reliable transport and
provides framing already.

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
---------------------

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
---------------

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