The OpenSwitcher TCP protocol
=============================

The OpenSwitcher application can communicate with the openswitcher_proxy service using the custom TCP protocol.
This protocol is inspired by the USB transport protocol that the ATEM Mini switchers can use. It's the higher
level protocol with all the counters and handshaking removed that were required for the UDP protocol reliability.

Packet format
-------------

The packets in the TCP protocol are a 2 byte header that's just the data length, and then the data itself.

This data is the normal high level ATEM packets that are a series of [length][padding][4-letter code][data] sections.

Initial connection
------------------

The main difference between the TCP and the UDP protocol is the handshake. The whole old low-level handshake is removed
and there's a new handshake based on high-level custom packets.

Connection start
^^^^^^^^^^^^^^^^

The client opens the connection to the proxy and sends a packet containing an empty field with the name '*SW*'.
The raw bytes for this packet would be:

.. code-block::

    00 08 00 08 00 00 2A 53 57 2A
    ^^^^^   TCP protocol packet length header
          ^^^^^ ATEM protocol length header
                ^^^^^ Padding
                      ^^^^^^^^^^^^ The *SW* as ascii

After this is sent the proxy will respond either with an authentication packet or a device listing depending on if
the `auth` setting is set to true in the proxy config

Authenticating
^^^^^^^^^^^^^^

If authentication is required the proxy will respond with this packet:

.. code-block::

    00 08 00 08 00 00 41 55 54 48
    ^^^^^   TCP protocol packet length header
          ^^^^^ ATEM protocol length header
                ^^^^^ Padding
                      ^^^^^^^^^^^^ The AUTH as ascii

When this packet is received the client is required to respond with a packet containing two fields.
The `*USR` field and the `*PWD` field.

.. code-block::

    00 1d 00 0d 00 00 2a 55 53 52 61 64 6d 69 6e 00 10 00 00 2a 50 57 44 70 61 73 73 77 6f 72 64
    ^^^^^   TCP protocol packet length header
          ^^^^^ ATEM protocol length header
                ^^^^^ Padding
                      ^^^^^^^^^^^^ The *USR as ascii
                                  ^^^^^^^^^^^^^^ The string "admin" as ascii
                                                 ^^^^^ The ATEM protocol length header for the second field
                                                       ^^^^^ Padding
                                                             ^^^^^^^^^^^ The *PWD as ascii

While it looks complex as a hexdump, it's possible to just re-use the field encoder for the switcher protocol itself
and prefix the packets with the 16 bit length before sending it out the TCP socket.

If the authentication is sucessful the proxy will respond with the device list the client would've gotten directly
if auth had been disabled. If the login credentials were incorrect the proxy will close the TCP connection.

Device list
^^^^^^^^^^^

In this phase the proxy will send a list of hardware that's exposed on the frontend with the `id` and the `label` for
the device. This is send as a single packet with a field in it for every device in the hardware list. The code for this
field is `*HW*`.

The contents of these fields is 40 bytes, these are 2 fixed length strings of 20 bytes containing the id and the label.

The labels of the devices are for showing a device picker in case the user has not selected a device yet when starting
the connection. the `id` needs to be sent to the proxy to select a device.

Selecting the device
^^^^^^^^^^^^^^^^^^^^

the final step of the handshake is the device selection. This is done by sending a packet with the `*DEV` field in it.
The contents of this field is the id string of the device (without the padding)

.. code-block::

    00 0c 00 0c 00 00 2a 44 45 56 6d 69 6e 69
    ^^^^^   TCP protocol packet length header
          ^^^^^ ATEM protocol length header
                ^^^^^ Padding
                      ^^^^^^^^^^^^ The *DEV as ascii
                                  ^^^^^^^^^^^ The string "mini" as ascii

After the client has sent this packet the protocol will switch over to relaying ATEM packets over the TCP connection.
This packet will also trigger sending the whole initial state of the device as a few large packets with a lot of fields
in them.