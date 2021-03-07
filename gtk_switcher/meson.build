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
    'preferenceswindow.py',
    'switcher.py',
    'media.py',
    'audio.py',
    'camera.py',
    'mixeffect.py',
    'upstreamkey.py',
    'colorwheel.py',
]

install_data(switcher_sources, install_dir: moduledir)
