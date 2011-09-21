from distutils.core import setup

pkg = 'Extensions.StreamInterface'
setup (name = 'enigma2-plugin-extensions-streaminterface',
       version = '0.1',
       description = 'StreamInterface',
       packages = [pkg],
       package_dir = {pkg: 'plugin'}
      )
