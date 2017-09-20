from setuptools import setup

setup(
    name='eschalon_utils',
    version='',
    packages=[''],
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
        'eschalon_b1_map.py',
        'eschalon_b2_map.py',
        'eschalon_b3_map.py',
        'eschalon_b1_char.py',
        'eschalon_b2_char.py',
        'eschalon_b3_char.py',
        'eschalon_utils.py',
    ],

)
