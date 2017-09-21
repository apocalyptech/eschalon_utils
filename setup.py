import eschalon
from setuptools import setup

setup(
    name='eschalon_utils',
    version=eschalon.version,
    packages=['eschalon_utils'],
    package_dir={'': 'tests'},
    url='',
    license='GPLv2+',
    author='',
    author_email='',
    description='',
    requires=[
        'Crypto',
    ],
    extras_require={
        'gui': [
            'pygtk>=2.18.0',
            'gobject',
            'numpy',
        ],
        'map': [
            'czipfile',
            'pycrypto',
        ]

    },
    scripts=[
        'eschalon_main.py',
        'eschalon_gui.py',
    ],
    tests_require= [
        'coverage'
    ]

)
