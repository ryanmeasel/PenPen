try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup('name': 'PenPen',
      'description': 'Audio podcasting suite.',
      'author': 'Ryan Measel',
      'url': 'https://github.com/ryanmeasel/PenPen',
      'author_email': 'ryanmeasel@gmail.com',
      'version': '0.0',
      'install_requires': ['mutagen==1.33.2']
      )
