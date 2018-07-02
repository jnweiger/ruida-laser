#! /usr/bin/python3
#
# proxy23.py -- listen for incoming udp/tcp packets and write them to file.
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


import os, sys, time, select
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

class RuidaProxyServer():
  NETWORK_TIMEOUT = 10000
  INADDR_ANY_DOTTED = '0.0.0.0'  # bind to all interfaces.
  SOURCE_PORT = 40200     # used by rdworks in Windows
  DEST_PORT   = 50200     # Ruida Board
  verbose = True          # babble while working
  chunkpause = 0.0        # 1.5        # seconds to wait between chunks. debugging only.
  ACK_BYTE = 0xc6
  NACK_BYTE = 0x46	  # csum error. FIXME: do we kow other error codes?
  CHUNK_SZ = 10000	  # max size per udp packet

  def __init__(self, port=DEST_PORT):
    localport = port

    self.udp_sock = socket(AF_INET, SOCK_DGRAM)
    self.udp_sock.setsockopt(SOL_SOCKET, socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.udp_sock.bind((self.INADDR_ANY_DOTTED, int(localport)))

    self.tcp_sock = socket(AF_INET, SOCK_STREAM)
    self.tcp_sock.setsockopt(SOL_SOCKET, socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.tcp_sock.bind((self.INADDR_ANY_DOTTED, int(localport)))
    self.tcp_sock.listen(5)
    self.tcp_conn = None
    self.busy = False
    self.output = None

  def _checksum(self, data, start, length):
    cs=sum(data[start:start+length])
    b1=cs & 0xff
    b0= (cs>>8) & 0xff
    return bytes([b0,b1])

  def find_end_token(data):
    if "\xd7" in data:
      return True
    False

proxy = RuidaProxyServer()

while True:
  ending = False
  inputs = [proxy.udp_sock, proxy.tcp_sock]
  if proxy.tcp_conn is not None:
    inputs.append(proxy.tcp_conn.fileno())

  try:
    inputready,outputready,exceptready = select.select(inputs, outputs, [])
  except select.error as e:
    break
  except socket.error as e:
    break

  if proxy.tcp_sock in inputready:
    conn, sender_addr = proxy.tcp_sock.accept()
    if proxy.busy:
      try:
        conn.send(proxy.NACK_BYTE)
      except:
        pass
      try:
        conn.shutdown(socket.SHUT_RDWR)
      except:
        pass
    else:
      # not yet busy
      proxy.tcp_conn = conn
      proxy.busy = True
      proxy.output = ( 0, sender_addr, "out_"+str(time.time())+".rd")
      proxy.output[0] = open(proxy.output[2], "w")
  # tcp_sock

  if proxy.busy and proxy.tcp_conn is not None and proxy.tcp_conn.fileno() in inputready:
    data = proxy.udp_sock.recv(proxy.CHUNK_SZ)
    proxy.output[0].write(data)
    proxy.tcp_conn.send(proxy.ACK_BYTE)
    ending = proxy.find_end_token(data)
  # tcp_conn

  if proxy.udp_sock in inputready:
    data, sender_addr = proxy.udp_sock.recvfrom(proxy.CHUNK_SZ)
    if proxy.busy:
      if proxy.output[1] == sender_addr:
        proxy.output[0].write(data)
        proxy.udp_sock.sendto(sender_addr, proxy.ACK_BYTE)
        ending = proxy.find_end_token(data)
      else:
        try:
          proxy.udp_sock.sendto(sender_addr, proxy.NACK_BYTE)
        except:
          pass
    else:
      # not yet busy
      proxy.busy = True
      proxy.output = ( 0, sender_addr, "out_"+str(time.time())+".rd")
      proxy.output[0] = open(proxy.output[2], "w")
      proxy.output[0].write(data)
      proxy.udp_sock.sendto(sender_addr, proxy.ACK_BYTE)
      ending = proxy.find_end_token(data)
  # udp_sock

  if ending:
    proxy.output[0].close()
    proxy.output = None
    proxy.busy = False

