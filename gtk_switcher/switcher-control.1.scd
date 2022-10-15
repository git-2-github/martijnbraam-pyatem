switcher-control(1) "switcher-control"

# NAME

switcher-control - graphical OpenSwitcher video switcher frontend

# SYNOPSIS

switcher-control [OPTIONS] [ip]

# DESCRIPTION

Switcher Control is a GTK application for controlling Blackmagic Design video switchers.

# OPTIONS

*-h, --help*
	Show the help message and quit

*--persist*
	Save the ip address for subsequent runs

*--debug*
	Output extra debugging info

*--dump [DUMP ...]*
	Dump raw data for specific protocol packets

*--view {switcher,media,audio,camera}*
	Start the application with a specific view open

*ip*
	The ip address of the switcher to connect to, can also be a proxy uri

# AUTHOR

Written by Martijn Braam

# COPYRIGHT

Copyright  ©  2022  Martijn Braam and the OpenSwitcher contributors
GPL version 3 only. <https://gnu.org/licenses/gpl.html>.
This is free software: you are free  to  change  and  redistribute  it.
There is NO WARRANTY, to the extent permitted by law.
