#! /usr/bin/python3
#
# udpsendruida.py -- send an rd file via udp.
# 2018 (C) juergen@fabmail.org
# Distribute under GPLv2 or ask.
#
# References (and thanks to):
# * https://wiki.fablab-nuernberg.de/w/Diskussion:Nova_35
# * https://github.com/kkaempf/LibLaserCut/tree/thunderlaser/src/com/t_oster/liblasercut/drivers/ruida
# 
# test against:
# ncat -l -u -v 50200

import sys
from socket import *

if len(sys.argv) < 3:
  print("Usage: %s IPADDR FILE.rd" % sys.argv[0])
  sys.exit(1)

host=sys.argv[1]
file=sys.argv[2]


class RuidaUdp():
  NETWORK_TIMEOUT = 3000
  INADDR_ANY_DOTTED = '0.0.0.0'  # bind to all interfaces.
  SOURCE_PORT = 40200     # used by rdworks in Windows
  DEST_PORT   = 50200     # Ruida Board
  MTU = 1470              # max data length per datagram (minus checksum)

  def __init__(self, host, port=DEST_PORT, localport=SOURCE_PORT):
    self.sock = socket(AF_INET, SOCK_DGRAM)
    self.sock.bind((self.INADDR_ANY_DOTTED, localport))
    self.sock.connect((host, port))

  def _checksum(self, data):
    cs=sum(data)
    b1=cs & 0xff
    b0= (cs>>8) & 0xff
    return bytes([b0,b1])

  def write(self, data):
    self.sock.send(data)

laser = RuidaUdp(host)
rdfile = open(file, 'rb').read()
laser.write(rdfile)
