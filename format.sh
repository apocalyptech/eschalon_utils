#!/bin/sh
autopep8 --in-place *.py */*.py
isort *.py */*.py
