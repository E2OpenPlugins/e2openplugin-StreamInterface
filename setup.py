from distutils.core import setup
import setup_translate

pkg = 'Extensions.StreamInterface'
setup(name='enigma2-plugin-extensions-streaminterface',
       version='0.2',
       description='StreamInterface',
       package_dir={pkg: 'plugin'},
       packages=[pkg],
       package_data={pkg: 
           ['stream.png', 'locale/*/LC_MESSAGES/*.mo']},
       cmdclass=setup_translate.cmdclass, # for translation
      )
