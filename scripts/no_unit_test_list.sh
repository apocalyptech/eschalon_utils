#!/bin/sh

# Not everything is unit tested (yet) so help capture errors by running things that should not error. Eventualy add unit tests...

python3 -m eschalon.main --book 1 --list all test_data/book1_atend.char
python3 -m eschalon.main --book 2 --list all test_data/book2_atend.char
python3 -m eschalon.main --book 3 --list all test_data/book3_f4_example.char
