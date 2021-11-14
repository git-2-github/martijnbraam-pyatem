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
