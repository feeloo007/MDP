from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='import_v2_intraparis_to_dca',
      version=version,
      description="Import des INTRAPARIS V2 dans l'application DCA",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Philippe GONCALVES',
      author_email='philippe.gonclaves@paris.fr',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
	'Fabric',
	'lxml',
	'html5lib',
	'basen',
	'pycolors2',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
