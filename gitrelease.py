#!/usr/bin/env python
# vim: set expandtab tabstop=4 shiftwidth=4:


import re
import subprocess
import sys


def usage():
    """
    Just prints out our usage and returns
    """
    print()
    print(("USAGE: %s <version>" % (sys.argv[0])))
    print()
    print(("ie: %s 0.8.0" % (sys.argv[0])))
    print()
    print("Note that the version MUST currently be three numbers")
    print("separated by digits")
    print()
    sys.exit()


# Check our args for validity
if len(sys.argv) != 2:
    usage()

version = sys.argv[1]
if not re.search('^\d+\.\d+\.\d+$', sys.argv[1]):
    usage()

# Now a bunch of vars
tagversion = version.replace('.', '-')
tag = 'Eschalon-%s' % tagversion
file_base = 'eschalon_utils-%s' % version
file_tar = '%s.tar' % file_base
file_tgz = '%s.gz' % file_tar
file_zip = '%s.zip' % file_base
archive_prefix = '--prefix=%s/' % file_base

# Create the git tag
subprocess.call(['git', 'tag', tag])
print(('Created tag %s' % tag))

# Build a .tar.gz
subprocess.call(['git', 'archive', '--format=tar',
                 archive_prefix, '-o', file_tar, tag])
subprocess.call(['gzip', file_tar])
print(('Wrote to %s' % file_tgz))

# Build a .zip
subprocess.call(['git', 'archive', '--format=zip',
                 archive_prefix, '-o', file_zip, tag])
print(('Wrote to %s' % file_zip))

# Finish
print()
print("Don't forget to 'git push --tags' if everything is kosher")
