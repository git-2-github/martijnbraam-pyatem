Using the Python module
=======================

The Switcher application is mainly to validate the correctness of the pyatem Python module. The python
code is split up in multiple modules. `pyatem.transport` handles the low level UDP protocol that adds
reliability on top of UDP. The `pyatem.protocol` module handles encoding and decoding commands and fields
for the mixers. The `pyatem.field` and `pyatem.command` module contain the encoders and decoders for all
the specific fields the switchers support.

Connecting
----------

To connect to the mixer you make an instance of the ``pyatem.protocol.AtemProtocol`` class and call the connect
method

.. code-block:: python

   from pyatem.protocol import AtemProtocol

   switcher = AtemProtocol("192.168.2.1")
   switcher.connect()
   while True:
     switcher.loop()

The connect command will send the first packet to the switcher, the loop method will process one incoming
packet every time it's called. It should be called at least once every second to prevent the connection
to the switcher disconnecting due to timeouts.

Receiving state changes
-----------------------

To have your application respond to changes in the mixer you can subscribe to events.

.. code-block:: python

   from pyatem.protocol import AtemProtocol

   def something_happened(field):
     print(field)

   switcher = AtemProtocol("192.168.2.1")

   # Register the event handler before connecting so you won't miss any events
   switcher.on("change", something_happened)

   switcher.connect()
   while True:
     switcher.loop()

The `change` event is the most generic one and will get called for every changed field the switcher will send.

To register event handlers for more specific fields you can set the field names:

.. code-block:: python

   from pyatem.protocol import AtemProtocol

   def video_mode_changed(mode):
     print(f"New video mode is {mode.get_label()}")
     if mode.rate > 30:
       print(":O so smooth")

   def program_bus_me1_changed(state):
     print(f"New program source is {state.source}")

   switcher = AtemProtocol("192.168.2.1")

   # The format is change:{fieldname} to get all changes for a field
   switcher.on("change:video-mode", video_mode_changed)

   # For some fields it's possible to get the event for only a specific index
   switcher.on("change:program-bus-input:0", program_bus_me1_changed)

   switcher.connect()
   while True:
     switcher.loop()

The names of the events are related to the decoder classes listed in the documentation. For example
the `VideoModeField` will be `change:video-mode` and the `KeyOnAirField` will be `change:key-on-air`

Sending commands
----------------

Sending commands is done by making instances of the classes in `pyatem.command.*` and passing those to
the connection object:

.. code-block:: python

   from pyatem.command import WipeSettingsCommand

   # Set the wipe softness on M/E 1
   cmd = WipeSettingsCommand(index=0, softness=400)
   
   switcher.send_commands([cmd])

The `send_commands` call accepts a list of command objects to send. If multiple commands are specified
in the list they will be send in a single network packet. This is useful to make sure changes happen at
the exact same time.
