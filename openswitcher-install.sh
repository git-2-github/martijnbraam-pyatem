#!/bin/sh

# This scripts installs the openswitcher components on the local system.

printf "Installing the pyatem module using setup.py install\n"
python3 setup.py build
sudo python3 setup.py install

printf "Installing the openswitcher application to /usr/local/\n"
meson _build
meson compile -C _build
sudo meson install -C _build

printf "*------------------------------------*\n"
printf "Installnstallation done\n"
printf "The python module is now available system-wide as 'pyatem'\n"
printf "The GTK application is now available as 'switcher-control'\n"
printf "The proxy application is now available as 'openswitcher-proxy'\n"