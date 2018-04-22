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
    self.sock.settimeout(self.NETWORK_TIMEOUT * 0.001)
    # timeval = struct.pack('ll', 2, 100)
    # self.sock.setsockopt(SOL_SOCKET, SO_RCVTIMEO, timeval)

  def _checksum(self, data, start, length):
    cs=sum(data[start:start+length])
    b1=cs & 0xff
    b0= (cs>>8) & 0xff
    return bytes([b0,b1])

  def write(self, data):
    start = 0
    l = len(data)
    while start < l:
      chunk_sz = l - start
      if chunk_sz > self.MTU:
        chunk_sz = self.MTU
      chksum = self._checksum(data, start, chunk_sz)
      buf = chksum + data[start:start+chunk_sz]
      self.send(buf)
      start += chunk_sz

  def send(self, ary):
    while True:
      self.sock.send(ary)
      try:
        data = self.sock.recv(8)     # timeout raises an exception
      except Exception as e:
        print("RuidaUdp.send", e)
        break
      l = len(data)
      if l == 0:
        print("received nothing")
        break
      # l == 1
      if data[0] == 0x46:           # 'F'
        raise IOError("checksum error")
      elif data[0] == 0xc6:
        # print("received ACK");
        break
      else:
        print("unknown response %02x\n" % data[0])
        break


laser = RuidaUdp(host)
rdfile = open(file, 'rb').read()
laser.write(rdfile)
