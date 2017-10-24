#!/bin/sh
set -e
mdl .
python setup.py check
python setup.py isort
nosetests-3.6 -c --with-coverage --with-id --detailed-errors --logging-clear-handlers "$@"
