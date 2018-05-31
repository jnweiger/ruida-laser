#! /usr/bin/python3
#
# udpreceiveruida.py -- listen for incoming udp/tcp packets and write them to file.
# 2018 (C) juergen@fabmail.org
# Distribute under GPLv2 or ask.
#
# References (and thanks to):
# * https://wiki.fablab-nuernberg.de/w/Diskussion:Nova_35
# * https://github.com/kkaempf/LibLaserCut/tree/thunderlaser/src/com/t_oster/liblasercut/drivers/ruida
#
#
# This listens at port 50200 both tcp and udp.
# For udp connections it sends responses to both, the sender port, and port 40200 
# of the sender IP if different.
#
# A TCP stream ends when the connection is closed.
# A UDP stream ends when there is a pause for more than 10 seconds, or when an
#      END command is seen in the stream.
#      Finish e7 00                            eb e7 00
#      Work_Interval 01 06 20 348.0mm 348.0mm  da 01 06 20 00 00 00 02 5c 00 00 00 02 5c
#      Run                                     d7

#
# All received files are written to files named IPADDR_TSTAMP.rd
# Multiple files can be received simultaneously from different sources.
# 
# - Each UDP packet is acknowledged with a single byte response packet:
#   0xc6 if all is well, 0x46 if checksum error.
#   The last packet is only acknowledged after the save routine is done.
# - If an END command is seen on a TCP connection, the save routine is started. 
#   if successful and the stream is still open, one 0xc6/0xc4 response is sent back.


import os, sys, time
from socket import *

if sys.version_info.major < 3:
  print("Need python3 for "+sys.argv[0])
  sys.exit(1)

if len(sys.argv) < 3:
  print("Usage: %s DIR/FILE_Prefix" % sys.argv[0])
  sys.exit(1)

## Nova35_Veitsbronn            192.168.2.21:50200
## Nova35_Proxy_Veitsbronn      192.168.2.23:50200
## Nova35_FabLabNbg             172.18.16.11:50200
## Nova35_Proxy_FabLabNbg       172.18.16.23:50200

class RuidaUdpServer():
  NETWORK_TIMEOUT = 10000
  INADDR_ANY_DOTTED = '0.0.0.0'  # bind to all interfaces.
  SOURCE_PORT = 40200     # used by rdworks in Windows
  DEST_PORT   = 50200     # Ruida Board
  verbose = True          # babble while working
  chunkpause = 0.0        # 1.5        # seconds to wait between chunks. debugging only.

  def __init__(self, port=DEST_PORT):
    localport = port

    self.udp_sock = socket(AF_INET, SOCK_DGRAM)
    self.udp_sock.setsockopt(SOL_SOCKET, socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.udp_sock.bind((self.INADDR_ANY_DOTTED, int(localport)))

    self.tcp_sock = socket(AF_INET, SOCK_STREAM)
    self.tcp_sock.setsockopt(SOL_SOCKET, socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.tcp_sock.bind((self.INADDR_ANY_DOTTED, int(localport)))
    self.tcp_sock.listen(5)

  def _checksum(self, data, start, length):
    cs=sum(data[start:start+length])
    b1=cs & 0xff
    b0= (cs>>8) & 0xff
    return bytes([b0,b1])

proxy = RuidaUdpServer()

# TODO: create a connection object per incoming connection.
