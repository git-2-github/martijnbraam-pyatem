Media upload and download
=========================

For the media stills there's an upload and download protocol and a custom compression format.

Frame format
------------

The frames are stored as 10-bit YCbCr data 4:2:2 with an alpha channel. This seems to also be a custom packing method
from Blackmagic Design. It packs 2 luma channels, 2 alpha channels and the Cb and Cr channel in 64 bits.

For the color conversion BT.709 coefficients are used.

If you look at the bits of 2 consecutive pixels, which is 8 bytes:

+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|0|1|2|3|4|5|6|7|0|1|2|3|4|5|6|7|0|1|2|3|4|5|6|7|0|1|2|3|4|5|6|7|
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| byte 1        |  byte 2       | byte 3        | byte 4        |
+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
| A1  (12 bits)         | Cb  (10 bits)     | Y 1  (10 bits)    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| A2  (12 bits)         | Cr  (10 bits)     | Y 2  (10 bits)    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

The color and luma channel are stored in limited range and the alpha is stored full range. The images use the
BT.709 colorspace

Compression
-----------

All the image format processing and scaling is done in the ATEM Software Control application, the hardware only ever
sees the Blackmagic Design YCbCr pixels. To speed up the network transfer a custom lossless compression scheme is used.

This custom compression format is a basic RLE compressor that works on 64 bit blocks, which neatly aligns with the
format of the image data.

All data is passed through directly in the decompressor unless a RLE header is detected, the RLE header is 8 bytes of
``0xFE``.

+----+----+----+----+----+----+----+----+-----------------------+
| B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | Note                  |
+====+====+====+====+====+====+====+====+=======================+
| 3A | 96 | 64 | FA | 3A | 9E | FC | FA | 2 fully red pixels    |
+----+----+----+----+----+----+----+----+-----------------------+
| FE | FE | FE | FE | FE | FE | FE | FE | RLE header            |
+----+----+----+----+----+----+----+----+-----------------------+
| 00 | 00 | 00 | 00 | 00 | 00 | 00 | FF | Repeat next 255 times |
+----+----+----+----+----+----+----+----+-----------------------+
| 3A | 96 | 64 | FA | 3A | 9E | FC | FA | the red pixel again   |
+----+----+----+----+----+----+----+----+-----------------------+

In this example there's 2 pixels first, which is just regular image data. Then an RLE header
to start a repeat. Then the next 8 bytes are the repeat count, there does not seem to be a
limit on how many repeats are possible as long as the count fits in 8 bytes. Then a image data block that is to be
repeated. The block that's repeated is always a 2-pixel (8 byte) block so the compression is mostly useful to compress
large swatches of a single color.

In practice with this compression scheme a solid color frame of any size can be compressed down to 24 bytes (a single
RLE header, the repeat count for the full image and a single block with the color for the image). Photographic content
is barely compressible. Vertical gradients are very compressible, horizontal gradients are not compressible at all.

Frame storage locking
---------------------

To upload or download frames from the memory in the ATEM the control software first need to obtain a lock to the
specific storage. The options for the storage for the lock is ``0`` for the media frame storage and ``255`` for
the macro storage.

The process for getting a lock is:

#. Check the LKST field first to see if the storage is locked. If another application has a lock the only thing
   you can do is wait for the LKST to update when the other application releases the lock.
#. Send a LOCK or PLCK command to get a lock on the storage.
#. At this point you should get an LKST and LKOB field back, the LKST telling you that someone has a lock and LKOB
   that tells you that you're the one with the lock.
#. Send or receive as many frames as you want if you did LOCK or a single frame when you did PLCK. The process for the
   upload and download is described in the sections below
#. If you obtained the lock using the LOCK command then here you also release the lock using LOCK again. If you used
   PLCK then the lock is automatically released.

Downloading a frame
-------------------

To download a frame after aquiring the lock you send an FTSU command which requests the download of a frame from the
hardware. This command requires the store ID, which is 0 for frame storage and the index which is the number of the
media still slot.

After sending FTSU the hardware should sending the frame using the FTDa packet. If the frame is larger than the packet
size the hardware will send multiple FTDa packets. When receiving the FTDa packet the software should respond with
FTUA to ack the chunks.

When all chunks have been sent the hardware will send an FTDC field to signify a sucessful transfer. If anything goes
wrong during the transfer a FTDE field will be sent with an error code.

Uploading a frame
-----------------

To upload a frame the first command is FTSD. If the transfer is accepted the hardware will respond with FTCD which
tells the software what the maximum data size per packet is and how many packets the software is allowed to send. During
the transfer you might receive multiple FTCD fields to adjust the packet size or to allow more packets to be sent.

After receiving the FTCD the frame needs to be chunked up into FTDa packets that are no larger than the size defined
in the FTCD and then sent out to the hardware. The hardware might send a chunk size that is not divisible by 8, make
sure the chunk size is rounded down to the nearest multiple of 8 before using it.

It's very important to make sure that the chunking of the data does not create a split in the middle of an RLE block
when using compressed frames. If the RLE header is in the last 24 bytes of a chunk the chunk should be made smaller
so that header sits at the start of the next chunk. If a RLE block is split up the hardware will lock up until it is
power-cycled.

Sending the FTDa packets too quickly might also lock up the hardware. These limits are different between the USB and
UDP protocol and might be different in third party protocol implementations. If there are random freezes of the hardware
during upload there might need to be a delay of a few miliseconds after sending the FTDa packets.

After all the FTDa packets have been sent out the last command is the FTFD command. This contains the name of the frame
that was just uploaded which will be displayed in the UI and it contains an MD5 hash of the data. This is the MD5 hash
of the YCbCrA encoded pixels *before* running the RLE compressor over it.

If everything went sucessful the hardware will respond with FTDC and the new frame will usable in the hardware. If
the hash was incorrect the hardware will just not respond at all.