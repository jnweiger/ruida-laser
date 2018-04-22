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
#
# Protocol specifications:
# - The device listens on a fixed UDP port (DEST_PORT). IPaddress is configurable, netmask is 255.255.255.0 fixed.
# - An RD file is transfered as payload, same commands and syntax as with USB-Serial or USB-MassStorage.
# - The payload is split in chunks with a well known maximum size (MTU). (The last packet is usually shorter)
# - There is no header, and no arbitration phase, but successful transmission of the first chunk indicates device ready.
# - Each chunk starts with a two byte checksum, followed by payload data. Length of the payload is implicit by the
#   UDP datagram size. (Would not work with TCP)
# - Each chunk is acknowledged with a single byte response packet:
#   0xc6 if all is well, The next chunk should be sent. TODO: Within a timout?
#   0x46 if error. TODO: Checksum error and/or busy?
# - The first chunk should be retried when 0x46 was received. For subsequent chunks transmission should be aborted.
# - TODO: is a pause needed after the last chunk before the next paylod can be sent?
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
      self.send(buf, retry=(start == 0))
      start += chunk_sz

  def send(self, ary, retry=False):
    retry_delay_sec = 0.2
    retry_delay_sec_max = 5.0
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
        if retry:
          print("retrying ...")
          time.sleep(retry_delay_sec)   # truncated binary backoff
          if retry_delay_sec < retry_delay_sec_max: retry_delay_sec *= 2
        else:
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
