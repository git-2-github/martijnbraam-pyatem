openswitcher-proxy(1) "openswitcher-proxy"

# NAME

openswitcher-proxy - Multi-protocol proxy for Blackmagic Design hardware

# SYNOPSIS

openswitcher-proxy [OPTIONS]

# DESCRIPTION

OpenSwitcher Proxy is a daemon that acts as a reverse proxy for the ATEM network protocol. It adds a layer of
authentication on top with the custom TCP protocol to safely run the protocol over the internet.

The proxy also supports connecting the ATEM system to other protocols like midi and mqtt for integrating in a
larger production environment

# OPTIONS

*-h, --help*
	Show the help message and quit

*--config CONFIGFILE*
	Config file to use

# AUTHOR

Written by Martijn Braam

# COPYRIGHT

Copyright  ©  2022  Martijn Braam and the OpenSwitcher contributors
GPL version 3 only. <https://gnu.org/licenses/gpl.html>.
This is free software: you are free  to  change  and  redistribute  it.
There is NO WARRANTY, to the extent permitted by law.
