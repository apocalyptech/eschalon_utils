#!/bin/sh
mypy -m eschalon.main --show-column-numbers -i --show-error-context "$@"
