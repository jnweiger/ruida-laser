#! /usr/bin/python3
#
# hexparser.py
#
# Direction from us to laser has leading checksum, two bytes.
# Direction from laser to us is without checksum.

import sys, re, binascii, time
from ruidaparser import RuidaParser

r = RuidaParser()
buf = sys.argv[1]



def check_checksum(data):
    sum = 0
    for i in bytes(data[2:]):
        sum += i & 0xff     # unsigned
    seen = ((data[0] & 0xff) << 8) + (data[1] & 0xff)
    if seen == sum:
        return data[2:]
    return None


def hexdecode_rd(buf, with_checksum=False):
    # weed out all non-hex chars and convert to binary string
    seen = buf = re.sub(r'[^a-f0-9]', '', buf.lower())     # '<D4 09 89 8D 89 89 89 8D 2B' -> 'd409898d8989898d2b'
    buf = binascii.a2b_hex(buf)                     #  -> b'\xd4\t\x89\x8d\x89\x89\x89\x8d+'
    if with_checksum:
      buf = check_checksum(buf)
      if not buf:
        print("hexdecode_rd: error: 2 bytes checksum does not match what follows in '%s'" % seen, flush=True)
        return None
    buf = r.unscramble_bytes(buf)                   #  -> b'\xda\x01\x00\x04\x00\x00\x00\x04#'
    return buf

if buf == "-":
  while True:
    buf = sys.stdin.readline()
    if buf == '':
      break
    print(buf, end='', flush=True)
    if buf[0] in ('<', '>'):

      unscambled = hexdecode_rd(buf, with_checksum=(buf[0] == '>'))
      unscambled_hex = binascii.b2a_hex(unscambled, ' ')               #  -> b'da 01 00 04 00 00 00 04 23'
      print('\t\t unscrambled:' + buf[0] + unscambled_hex.decode('utf-8'), flush=True)
      try:
        r.decode(unscambled, debug=True)
      except:
        print("r.decode failed\n", flush=True)
        pass
    else:
      time.sleep(0.01)

else:
  hexdecode_rd(buf)


if False:
  from pprint import pprint
  pprint({ 'p':r._paths, 'bbox':r._bbox, 'las':r._laser}, depth=5, stream=sys.stderr, flush=True)

###

