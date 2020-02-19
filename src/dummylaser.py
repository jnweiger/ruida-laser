#! /usr/bin/python3
#
# thunderlaserdummy.py
#
# Prepare a loopback network like this:
#   sudo ifconfig lo:1 192.168.2.21 up       # falafue
#   sudo ifconfig lo:1 172.22.30.12 up       # fababnbg
#

from __future__ import print_function

import socket, sys

ip_addr = '192.168.2.21'                # falafue
# ip_addr = '172.22.30.12'                # fablabnbg
server_port = 50200
mtu = 1470

def unscramble(b):
    """ unscramble a single byte for reading from *.rd files """
    res_b=b-1
    if res_b<0: res_b+=0x100
    res_b^=0x88
    fb=res_b&0x80
    lb=res_b&1
    res_b=res_b-fb-lb
    res_b|=lb<<7
    res_b|=fb>>7
    return res_b

def unscramble_bytes(data):
    if sys.version_info.major < 3:
      return bytes([unscramble(ord(b)) for b in data])
    else:
      return bytes([unscramble(b) for b in data])

def check_checksum(data):
  sum = 0
  for i in bytes(data[2:]):
    sum += i & 0xff     # unsigned
  seen = ((data[0] & 0xff) << 8) + (data[1] & 0xff)
  if seen == sum:
    return data[2:]
  return None


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
if hasattr(socket, "SO_REUSEPORT"):
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
print("sock.bind %s:%d ..." % (ip_addr, server_port), end="")
sock.bind((ip_addr, server_port))
print(" listening ...")


# somebody does 
#   sock.sendto(b"Hello World\n", (ip_addr, server_port))


while True:
    data, addr = sock.recvfrom(1024)
    buf = check_checksum(data)
    if buf is None:
      print("bad checksum in %s from %s" % (data, addr))
      sock.sendto(b'\x46', addr)     # reply 0x46=NACK
    else:
      buf = unscramble_bytes(buf)
      print("Seen: %s from %s" % (buf, addr))
      sock.sendto(b'\xc2', addr)     # reply 0xc2=ACK
