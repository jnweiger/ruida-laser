#! /usr/bin/python3
#
# hexparserd.py
#
import sys, re, binascii
from ruidaparser import RuidaParser

r = RuidaParser()
buf = sys.argv[1]

def hexdecode_rd(buf):
    # weed out all non-hex chars and convert to binary string
    buf = re.sub(r'[^a-f0-9]', '', buf.lower())     # '<D4 09 89 8D 89 89 89 8D 2B' -> 'd409898d8989898d2b'
    buf = binascii.a2b_hex(buf)                     #  -> b'\xd4\t\x89\x8d\x89\x89\x89\x8d+'
    buf = r.unscramble_bytes(buf)                   #  -> b'\xda\x01\x00\x04\x00\x00\x00\x04#'
    print(binascii.b2a_hex(buf, ' '))               #  -> b'da 01 00 04 00 00 00 04 23'
    # r.decode(buf, debug=True)

if buf == "-":
  while True:
    buf = sys.stdin.readline()
    if buf == '':
      break
    hexdecode_rd(buf)
else:
  hexdecode_rd(buf)


if False:
  from pprint import pprint
  pprint({ 'p':r._paths, 'bbox':r._bbox, 'las':r._laser}, depth=5, stream=sys.stderr)

###

