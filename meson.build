project('switcher',
    version: '0.4.0',
    meson_version: '>= 0.50.0',
    default_options: ['warning_level=2'])

dependency('libhandy-1', version: '>=1.0.0')

if get_option('with_gtk_app')
    subdir('data')
    subdir('gtk_switcher')
endif

if get_option('with_proxy')
    subdir('openswitcher_proxy')
endif

meson.add_install_script('build-aux/meson/postinstall.py')
