The low level UDP protocol
==========================

The ATEM Software Control application communicates with the mixer over a custom UDP protocol on port 9910.

Like most custom UDP protocols this is also a re-invention of TCP over UDP. It has implemented sequence numbers,
retransmissions and acknowledgements and an almost perfect copy of the TCP 3-way handshake to start the connection.

Anatomy of a packet
-------------------

+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|0|1|2|3|4|5|6|7|0|1|2|3|4|5|6|7|0|1|2|3|4|5|6|7|0|1|2|3|4|5|6|7|
+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
| flags   | packet length       | session                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| acknowledgement number        | unknown                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| remote sequence number        | local sequence number         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

This is the header for a packet in the UDP protocol, it's always 12 bytes long. Outgoing and incoming
packets have the exact same header format.

The flags field is a bitfield with these bits:

=== ======================= ===========
Bit Name                    Description
=== ======================= ===========
0   Reliable                The other end should respond with an ACK packet for this packet
1   SYN                     Used in the connection handshake
2   Retransmission          This packet is a retransmission of an earlier packet
3   Request retransmission  Request a retransmission of an earlier sequence id
4   ACK                     This packet is an ACK packet.
=== ======================= ===========

The packet length field is the size of the packet, including the 12 bytes of the header.

The session field is a 16 bit number that gets assigned to clients after the handshake. Clients are supposed
to start with a random session id in the handshake itself and after getting a session id from the switcher
expects all packets after that to have the right session id set.

The acknowledgement number field is used in combination with the ACK flag. If a packet has the ACK flag set
the acknowledgement number field will contain the number of the last received packet from the other end.

The remote sequence number is the value of the packet counter in switcher. On a perfect network connection this
should always increase by 1 for every packet received from the switcher. Otherwise a package might need to be 
requested for retransmission.

The local sequence number is the value of a counter of packets sent to the switcher. This value should be
incremented by one for every packet that's sent out EXCEPT for for packets that have the ACK flag set or the
SYN flag set.

Starting a connection
---------------------

The connection is made by a three way handshake

The first packet
^^^^^^^^^^^^^^^^

A connection is started by sending a packet to the mixer that has the SYN flag set, a random session id and
a specific payload

The payload for this packet should be `0x01 0x00 0x00 0x00 0x00 0x00 0x00 0x00`. 

The second packet
^^^^^^^^^^^^^^^^^

The switcher will respond with a packet with SYN set and matching the session id you sent in the first packet.

The first byte of data in this packet will be the connection status. On a successful connection this should be
`0x02`. If the switcher responds with `0x04` you should restart the connection.

The third packet
^^^^^^^^^^^^^^^^

As final step in the connection you should send back an ACK packet. After this your random session id is no
longer valid and the client should take the session id from the next packet the switcher sends.

Once the ACK has been sent the switcher will start dumping the full state of all fields in the switcher as a few
large packets, closing with an empty packet. Once this packet has been sent by the switcher you're required to
respond to packets with the Reliable flag set with an ACK, otherwise the switcher will assume you lost the packet
and try to resend it.

This first empty packet should also be responded to with a special crafted ACK packet (yes an ACK to the ACK). This
packet should have the ACK flag set, the acknowledgement number set to the remove sequence number and the remote
sequence number of this packet should be set to `0x61`. This is the only packet where the client sets a value in
the remote sequence number field of the header.

.. _high-level-protocol:

The higher level protocol
-------------------------

All packets that are longer than 12 bytes contain fields or commands. These are sent as a 16 bit length of the field/command, 2 unknown bytes which are most likely padding and 4 ASCII characters signifying the field/command type.

+---------------+-------------+------------+-----------+
| Byte 1        |   Byte 2    |   Byte 3   | Byte 4    |
+===============+=============+============+===========+
| Field length                |  Padding bytes         |
+---------------+-------------+------------+-----------+
| Field type as 4 ASCII characters                     |
+---------------+-------------+------------+-----------+
| Field data, field-length-8 bytes long                |
+---------------+-------------+------------+-----------+

Packets can have multiple fields or commands in them and they are just concatenated together. To parse a packet from
the mixer keep decoding fields from the packet until the end of the packet is reached.

The commands that are sent back from the client to the switcher are the exact same format.

The decoding of the field data inside the fields is described in the rest of the pages of this documentation.
