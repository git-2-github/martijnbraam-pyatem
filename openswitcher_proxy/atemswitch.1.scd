atemswitch(1) "atemswitch"

# NAME

atemswitch - CLI client for the OpenSwitcher proxy HTTP api

# SYNOPSIS

atemswitch [OPTIONS]

# DESCRIPTION

The atemswitch utility provides a convenient way to use the OpenSwitcher Proxy http api module to trigger
switches from your own scripts. This only implements the CUT and AUTO functionality to have minimal easy to use
command line interface.

# OPTIONS

*-h, --help*
	Show the help message and quit

*-s URI, --proxy URI*
	HTTP uri to the root of the openswitcher proxy http API, required

*-t INPUT, --to-source INPUT*
	Input number or name of the source to switch to, required

*-u USERNAME, --username USERNAME*
	Authentication username for the proxy http api

*-p PASSWORD, --password PASSWORD*
	Authentication password for the proxy http api

*-a, --auto*
	Do an AUTO transition instead of a CUT transition

*-i INDEX, --index INDEX*
	Use a different M/E index, the M/E units are zero-indexed and this utility defaults to the first M/E

# AUTHOR

Written by Martijn Braam

# COPYRIGHT

Copyright  ©  2022  Martijn Braam and the OpenSwitcher contributors
GPL version 3 only. <https://gnu.org/licenses/gpl.html>.
This is free software: you are free  to  change  and  redistribute  it.
There is NO WARRANTY, to the extent permitted by law.
