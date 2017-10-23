#!/bin/sh
mypy -m eschalon.main --show-column-numbers -v -i --show-error-context --strict "$@"
