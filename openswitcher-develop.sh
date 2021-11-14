#!/bin/sh

# This tool sets up openswitcher and pyatem to run from the source files in the git repository. This requires root
# permissions to install the software using symlinks to the source.

printf "Installing the pyatem module using setup.py develop\n"
sudo python3 setup.py develop

printf "Installing the openswitcher application to /usr/local/\n"
meson _build
meson compile -C _build
sudo meson install -C _build

printf "*------------------------------------*\n"
printf "Development installation done\n"
printf "The python module is now available system-wide as 'pyatem'\n"
printf "The GTK application is now available as 'switcher-control'\n"
printf "The proxy application is now available as 'openswitcher-proxy'\n"