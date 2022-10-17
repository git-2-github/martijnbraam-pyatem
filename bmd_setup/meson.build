# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'bmd_setup')
gnome = import('gnome')

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
    input: 'bmd-setup.in',
    output: 'bmd-setup',
    configuration: conf,
    install: true,
    install_dir: get_option('bindir')
)

setup_sources = [
    '__init__.py',
    '__main__.py',
    'window.py',
]

install_data(setup_sources, install_dir: moduledir)

subdir('data')

scdoc = dependency('scdoc', native: true, required: get_option('man-pages'))
if scdoc.found()
  scdoc_prog = find_program(scdoc.get_pkgconfig_variable('scdoc'), native: true)
  mandir = get_option('mandir')
  man_files = [
            'bmd-setup.1.scd',
  ]
  foreach filename : man_files
    topic = filename.split('.')[-3].split('/')[-1]
    section = filename.split('.')[-2]
    output = '@0@.@1@'.format(topic, section)

    custom_target(
      output,
      input: filename,
      output: output,
      feed: true,
      capture: true,
      command: scdoc_prog.path(),
      install: true,
      install_dir: '@0@/man@1@'.format(mandir, section)
    )
  endforeach
endif