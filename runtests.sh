#!/bin/sh
set -e
python setup.py check
python setup.py isort
nosetests-3.7 -c --with-coverage --with-id --detailed-errors --logging-clear-handlers "$@"
