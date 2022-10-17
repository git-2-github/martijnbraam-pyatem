# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'gtk_switcher')
gnome = import('gnome')

gnome.compile_resources('atem',
    'atem.gresource.xml',
    gresource_bundle: true,
    install: true,
    install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
    input: 'switcher-control.in',
    output: 'switcher-control',
    configuration: conf,
    install: true,
    install_dir: get_option('bindir')
)

switcher_sources = [
    '__init__.py',
    '__main__.py',
    'atemwindow.py',
    'connectionwindow.py',
    'preferences.py',
    'switcher.py',
    'media.py',
    'audio.py',
    'camera.py',
    'mixeffect.py',
    'mixeffect_aux.py',
    'upstreamkey.py',
    'colorwheel.py',
    'layout.py',
    'decorators.py',
    'adjustmententry.py',
    'dial.py',
    'downstreamkey.py',
    'gtklogadjustment.py',
    'macroeditor.py',
    'stream_data.py',
    'template_i18n.py',
    'eqcurve.py',
    'eqwindow.py',
    'videohub.py',
    'videohubbus.py',
    'videohubconnection.py',
    'debugger.py',
]

install_data(switcher_sources, install_dir: moduledir)

scdoc = dependency('scdoc', native: true, required: get_option('man-pages'))
if scdoc.found()
  scdoc_prog = find_program(scdoc.get_pkgconfig_variable('scdoc'), native: true)
  mandir = get_option('mandir')
  man_files = [
            'switcher-control.1.scd',
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
