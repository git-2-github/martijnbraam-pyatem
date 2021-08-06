PyATEM
======

Library implementing the ATEM video switcher protocol and a GTK3.0 application

![Screenshot of the control application](https://brixit.nl/openatem.png)

Installation
------------

Install the pyatem protocol module::

    sudo setup.py install

Build and install the gtk application::

    meson build
    cd build
    ninja
    sudo ninja install

Run the application::

    switcher-control

Developing
----------

Development happens on matrix on #openatem:brixit.nl

Proxy
-----

There is also the `openswitcher_proxy` python module in this repository. It will run an API wrapper around one or
more ATEM switchers. There is currently a single api supported which is a HTTP REST api for sending commands and
reading the mixer state.

It can be run by starting the module::

    python3 -m openswitcher_proxy --config /etc/myconfigfile.toml

The default config location is /etc/openswitcher/proxy.conf if not specified. Here's an example config:

    [[hardware]]
    id = "mini"
    label = "Atem Mini"
    address = "192.168.2.84"

    [[hardware]]
    id = "mini2"
    label = "Local switcher"
    address = "usb"

    [[frontend]]
    type = "http-api"
    bind = ":8080"
    auth = true
    username = "bob"
    password = "hunter2"
    hardware = "mini,mini2"
     
    [[frontend]]
    type = "status"
    bind = "127.0.0.1:8082"
    auth = false

The status frontend provides a simple html page with the state of the connected switchers and a list
of the enabled frontends.

The http-api frontend provides a HTTP server that can return any of the supported fields as json and
trigger commands by sending a HTTP POST request with formfields or json