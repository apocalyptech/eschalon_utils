#!/bin/sh
autopep8 --in-place --max-line-length 120 *.py */*.py
isort *.py */*.py
