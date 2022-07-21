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