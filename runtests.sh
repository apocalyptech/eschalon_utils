#!/bin/sh
set -e
mdl .
python setup.py check
nosetests-2.7 -c --with-coverage --with-id --detailed-errors "$@"
nosetests-3.6 -c --with-coverage --with-id --detailed-errors "$@"
