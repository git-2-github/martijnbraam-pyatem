pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'openswitcher_proxy')

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
    input: 'openswitcher-proxy.in',
    output: 'openswitcher-proxy',
    configuration: conf,
    install: true,
    install_dir: get_option('bindir')
)

proxy_sources = [
    '__init__.py',
    '__main__.py',
    'frontend.py',
    'frontend_status.py',
    'frontend_tcp.py',
    'frontend_httpapi.py',
    'frontend_mqtt.py',
    'hardware.py',
    'error.py',

]

install_data(proxy_sources, install_dir: moduledir)

install_data(
    'cli-switch.py',
    install_dir: get_option('bindir'),
    install_mode: 'rwxr-xr-x',
    rename: ['atemswitch']
)

scdoc = dependency('scdoc', native: true, required: get_option('man-pages'))
if scdoc.found()
  scdoc_prog = find_program(scdoc.get_pkgconfig_variable('scdoc'), native: true)
  mandir = get_option('mandir')
  man_files = [
            'openswitcher-proxy.1.scd',
            'atemswitch.1.scd',
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