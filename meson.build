# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
project('switcher',
    version: '0.9.0',
    meson_version: '>= 0.50.0',
    default_options: ['warning_level=2'])

i18n = import('i18n')

dependency('libhandy-1', version: '>=1.0.0')

if get_option('with_gtk_app')
    subdir('data')
    subdir('gtk_switcher')
    subdir('po')
endif

if get_option('with_setup_app')
    subdir('bmd_setup')
endif


if get_option('with_proxy')
    subdir('openswitcher_proxy')
endif

meson.add_install_script('build-aux/meson/postinstall.py')
