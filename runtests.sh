#!/bin/sh
set -e
python setup.py check
nosetests-2.7 -c --with-coverage "$@"
nosetests-3.6 -c --with-coverage "$@"
