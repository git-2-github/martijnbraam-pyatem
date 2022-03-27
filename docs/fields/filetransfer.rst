File transfer fields
====================

The filetransfer fields are used for reading and writing static content to and
from the hardware. It is used for both the media pool and the macro pool.


Lock management
---------------

.. autoclass:: pyatem.field.LockStateField
   :members:

.. autoclass:: pyatem.field.LockObtainedField
   :members:

Data transfer
-------------

.. autoclass:: pyatem.field.FileTransferDataField
   :members:

.. autoclass:: pyatem.field.FileTransferDataCompleteField
   :members:

.. autoclass:: pyatem.field.FileTransferErrorField
   :members:

.. autoclass:: pyatem.field.FileTransferContinueDataField
   :members:

Pool settings
-------------

.. autoclass:: pyatem.field.MediaplayerFileInfoField
   :members:

.. autoclass:: pyatem.field.MacroPropertiesField
   :members:
