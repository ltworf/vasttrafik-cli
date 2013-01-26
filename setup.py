from distutils.core import setup

import glob

setup(name="PyVasttrafik",
      version="0.1",
      author="Salvo 'LtWorf' Tomaselli",
      author_email="tiposchi@tiscali.it",
      url="https://github.com/ltworf/pysttrafik",
      license="GNU General Public License Version 3 (GPLv3)",
      scripts=['bin/pyvasttrafik'],
      py_modules = ['gui', 'key', 'main', 'pysttrafik', 'selgui', 'stop_selector'],
      data_files=[
          ('icons', glob.glob('icons/*.png')),
          ('/usr/share/applications', ['bin/pyvasttrafik.desktop']),
      ],
)