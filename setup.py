import eschalon
from setuptools import setup

setup(
    name='eschalon_utils',
    version=eschalon.version,
    packages=['eschalon_utils'],
    package_dir={'': 'tests'},
    url='',
    license='',
    author='',
    author_email='',
    description='',
    requires=[
    ],
    extras_require={
        'gui': [
            'pygtk>=2.18.0',
        ],
        'map': [
            'czipfile',
            'pycrypto',

        ]

    },
    scripts=[
        'eschalon_map.py',
        'eschalon_char.py',
        'eschalon_utils.py',
    ],

)
