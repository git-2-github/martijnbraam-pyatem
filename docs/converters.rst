Converter setup protocol
========================

The Blackmagic design Mini and Micro converters have an USB port for firmware updates and some basic configuration.

The firmware update side is handled through the standardized DFU protocol and the the .bin files for the
converters are distributed with the offical setup applications. These can be extracted from the installer and
flashed using the regular dfu-utils methods.

The configuration protocol
--------------------------

The protocol for configuration is quite simple but it does require knowing in advance which settings exist on
the specific hardware and what the possible values are. This is hardcoded in the offical application.

The full protocol is build on top of control transfers. The settings are split up in two categories.
The only difference between these is different bmRequestType and bRequest values to read and write from them.

+-----------------------+-----------------+-----------------+
|                       | System setting  | Device setting  |
+=======================+=================+=================+
| bmRequestType r/w     | 0xA1 / 0x21     | 0xC0 / 0x40     |
+-----------------------+-----------------+-----------------+
| bRequest transaction  | 1               | 10              |
+-----------------------+-----------------+-----------------+
| bRequest name         | 2               | 11              |
+-----------------------+-----------------+-----------------+
| bRequest read         | 3               | 12              |
+-----------------------+-----------------+-----------------+
| bRequest write        | 4               | 13              |
+-----------------------+-----------------+-----------------+

The system settings are the device name, software version and build id. All the other settings are device
settings.

To do a setting read or write it is first required to get a transaction id. The transaction id is changed
after every single read and write to the device.

+---------------+------------------+----------------------------------+
| Type          | Control Transfer |                                  |
+===============+==================+==================================+
| bmRequestType | 0xA1 or 0xC0     | Depends on system/device setting |
+---------------+------------------+----------------------------------+
| bRequest      | 1 or 10          | Depends on system/device setting |
+---------------+------------------+----------------------------------+
| wValue        | 0x0000           |                                  |
+---------------+------------------+----------------------------------+
| wIndex        | 0x0000           |                                  |
+---------------+------------------+----------------------------------+
| wLength       | 2                |                                  |
+---------------+------------------+----------------------------------+

The result is a 2-byte transaction number that is required fo the further control transfers.

Reading a setting
-----------------

A setting read is done by first writing the ascii name of the setting to the device with a control
transfer and then reading back the result. Here is an example for reading the device name:

+---------------+------------------+----------------------------------------+
| Type          | Control Transfer |                                        |
+===============+==================+========================================+
| bmRequestType | 0xA1             | Because DeviceName is a system setting |
+---------------+------------------+----------------------------------------+
| bRequest      | 2                | bRequest for setting name              |
+---------------+------------------+----------------------------------------+
| wValue        | xxx              | This is the transaction ID             |
+---------------+------------------+----------------------------------------+
| wIndex        | 0x0000           |                                        |
+---------------+------------------+----------------------------------------+
| wLength       | 10               |                                        |
+---------------+------------------+----------------------------------------+
| Data          | DeviceName       | Name of the setting                    |
+---------------+------------------+----------------------------------------+

Now the value can be read back by doing another control transfer

+---------------+------------------+----------------------------------------+
| Type          | Control Transfer |                                        |
+===============+==================+========================================+
| bmRequestType | 0x21             | Because DeviceName is a system setting |
+---------------+------------------+----------------------------------------+
| bRequest      | 3                | bRequest for setting read              |
+---------------+------------------+----------------------------------------+
| wValue        | xxx              | This is the transaction ID             |
+---------------+------------------+----------------------------------------+
| wIndex        | 0x0000           |                                        |
+---------------+------------------+----------------------------------------+
| wLength       | 255              | Max length of the name                 |
+---------------+------------------+----------------------------------------+

The resulting data will be the value of the setting.

Writing a setting
-----------------
A setting write is done by writing the name of the setting with a control transfer and then
writing the value of that setting with another control transfer.

Here is an example for writing the device name:

+---------------+------------------+----------------------------------------+
| Type          | Control Transfer |                                        |
+===============+==================+========================================+
| bmRequestType | 0xA1             | Because DeviceName is a system setting |
+---------------+------------------+----------------------------------------+
| bRequest      | 2                | bRequest for setting name              |
+---------------+------------------+----------------------------------------+
| wValue        | xxx              | This is the transaction ID             |
+---------------+------------------+----------------------------------------+
| wIndex        | 0x0000           |                                        |
+---------------+------------------+----------------------------------------+
| wLength       | 10               |                                        |
+---------------+------------------+----------------------------------------+
| Data          | DeviceName       | Name of the setting                    |
+---------------+------------------+----------------------------------------+

This control transfer was identical to the first control transfer for a setting read above.

Now the value needs to be written by a second control transfer:

+---------------+------------------+----------------------------------------+
| Type          | Control Transfer |                                        |
+===============+==================+========================================+
| bmRequestType | 0xA1             | Because DeviceName is a system setting |
+---------------+------------------+----------------------------------------+
| bRequest      | 4                | bRequest for setting write             |
+---------------+------------------+----------------------------------------+
| wValue        | xxx              | This is the transaction ID             |
+---------------+------------------+----------------------------------------+
| wIndex        | 0x0000           |                                        |
+---------------+------------------+----------------------------------------+
| wLength       | 7                |                                        |
+---------------+------------------+----------------------------------------+
| Data          | Example          | Sets the name to "Example"             |
+---------------+------------------+----------------------------------------+
