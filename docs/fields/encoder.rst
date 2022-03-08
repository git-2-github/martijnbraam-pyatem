Video encoder fields
====================

These are the fields related to the built in video encoder in the ATEM Mini series
of video switchers. This contains all the settings for the "Live stream" and
"Stream recorder" components of these devices.

The settings for these two features are interlinked. The same encoder is used
for creating the h265 stream for the live broadcast and the recording.


Base encoder settings
---------------------

.. autoclass:: pyatem.field.StreamingAudioBitrateField
   :members:

Live streaming
--------------

.. autoclass:: pyatem.field.StreamingServiceField
   :members:

.. autoclass:: pyatem.field.StreamingStatusField
   :members:

.. autoclass:: pyatem.field.StreamingStatsField
   :members:

Recording
---------

.. autoclass:: pyatem.field.RecordingSettingsField
   :members:

.. autoclass:: pyatem.field.RecordingDiskField
   :members:

.. autoclass:: pyatem.field.RecordingStatusField
   :members:

.. autoclass:: pyatem.field.RecordingDurationField
   :members:
