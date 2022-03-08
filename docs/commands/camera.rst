Camera control
==============

The camera control command is for sending commands to attached Blackmagic Design
cameras. On most ATEM hardware these commands are sent out over the program SDI
output and received on the SDI inputs of the cameras. The ATEM Mini series can
send the same commands over the HDMI inputs to attached Pocket Cinema cameras.

For connecting these two universes the Bidirectional SDI to HDMI mini converter
can be used.

.. autoclass:: pyatem.command.CameraControlCommand
   :members:
   :special-members:
