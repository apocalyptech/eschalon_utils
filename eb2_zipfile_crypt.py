#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:

# I believe this to be AES-256 (in CBC mode).  It uses PKCS7 padding for
# the data.
#
# The use of an IV here is kind of stupid, given the application,
# but whatever.
#
# Constructed mostly from
# http://www.codekoala.com/blog/2009/aes-encryption-python-using-pycrypto/
# ... the comments in particular contained a lot of info, and links to
# other resources.
#
# Windows PyCrypto binaries at
# http://www.voidspace.org.uk/python/modules.shtml#pycrypto

# First runthrough:
# Secret: ZOzND3khdZGyczSal4TakWqzSCPXpCyPwuNcHb_zPrk=
# Encrypted: 2Am9Pff522Nn7JTsjxiNdwQsJsW9aa7VaWaPl0qaiEcvqRC5r3lcKdWXNrrlJhtm

import os
import base64
from Crypto.Cipher import AES

plain_text = '_Sr1g@As_!IzCE-"<;!Q'
block_size = 16
key_size = 32
mode = AES.MODE_CBC

# Get our secret
secret = os.urandom(key_size)
secret_b64 = base64.urlsafe_b64encode(secret)
print 'Secret: %s' % (secret_b64)

# IV
iv = os.urandom(block_size)
iv_b64 = base64.urlsafe_b64encode(iv)

# Figure out our pad, and do the padding
pad = block_size - len(plain_text) % block_size
data = plain_text + pad * chr(pad)

# Now actually encrypt
encrypted = iv + AES.new(secret, mode, iv).encrypt(data)
encrypted_b64 = base64.urlsafe_b64encode(encrypted)
print 'Encrypted: %s' % (encrypted_b64)
