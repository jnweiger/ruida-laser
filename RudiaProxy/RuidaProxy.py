#! /usr/bin/python3
#
# RudiaPrody.py -- listen for incoming udp packets and forward them bidirectionally.
# 2020 (C) juergen@fabmail.org
# Distribute under GPLv2 or ask.
#
# References (and thanks to):
# * https://wiki.fablab-nuernberg.de/w/Diskussion:Nova_35
# * https://github.com/kkaempf/LibLaserCut/tree/thunderlaser/src/com/t_oster/liblasercut/drivers/ruida
#
# This listens at port 50200 and 40200 udp.

# A UDP stream ends when there is a pause for more than 10 seconds, or when an
#      END command is seen in the stream.
#      Finish e7 00                            eb e7 00
#      Work_Interval 01 06 20 348.0mm 348.0mm  da 01 06 20 00 00 00 02 5c 00 00 00 02 5c
#      Run                                     d7
#
# We define a logical UDP "Stream" to have pauses shorter than 10 sec between packets.
#
# - Each UDP packet is acknowledged with a single byte response packet:
#   0xc6 if all is well, 0x46 if checksum error.
# - IF a UDP Stream already exists, additional incoming packets are NaK'ed with 0x46
#
# Clients send packets from port 50200 and the laser receives them at port 40200.
# Responses from the laser are sent from port 40200 and are received by the client at port 50200.
#
# Prepare a loopback network like this:
#   sudo ifconfig lo:2 172.22.30.50 netmask 255.255.255.0 up       # fababnbg
#
# 2020-02-18, v0.1, jw  - initial draught.

__version__ = "0.1"

import os, sys, time, select
from socket import *

INADDR_ANY_DOTTED = '0.0.0.0'   # bind to all interfaces.
BUSY_TIMEOUT = 10.000           # seconds. A pause that long ends a UDP Stream.

if sys.version_info.major < 3:
  print("Need python3 for "+sys.argv[0])
  sys.exit(1)

if len(sys.argv) < 3:
  print("Usage: %s RUIDA_IP_ADDR [LISTEN_IP_ADDR]" % sys.argv[0])
  sys.exit(1)

class RuidaProxyServer():
  CLIENT_PORT = 40200      # used by rdworks in Windows to send and receive.
  RUIDA_PORT  = 50200      # Ruida Board receives and sends here.
  verbose = True          # babble while working
  ACK_BYTE = 0xc6
  ACK_TOKEN = b"\xc6"
  NACK_BYTE = 0x46	  # csum error. FIXME: do we kow other error codes?
  NACK_TOKEN = b"\x46"
  FIN_TOKEN = b"\xd7"      # the last packet in a transmission contains this.
  CHUNK_SZ = 4096       # whatever ...

  def __init__(self, listen=INADDR_ANY_DOTTED, dest="172.22.30.12"):
    self.dest = dest

    self.udp_backend_port = socket(AF_INET, SOCK_DGRAM)   # communication with laser
    self.udp_backend_port.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    self.udp_backend_port.bind((listen, int(self.CLIENT_PORT)))

    self.udp_frontend_port = socket(AF_INET, SOCK_DGRAM)    # communication with the world
    self.udp_frontend_port.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    self.udp_frontend_port.bind((listen, int(self.RUIDA_PORT)))
    print("RudiaPrody v%s listening on %s:{%d,%d} ..." % (__version__, listen, self.CLIENT_PORT, self.RUIDA_PORT))


listen_addr = INADDR_ANY_DOTTED
if len(sys.argv) > 2:
  listen_addr = sys.argv[2]

proxy = RuidaProxyServer(listen=listen_addr, dest=sys.argv[1])
last_pkg_tstamp = 0             # seconds since epoch
last_client_ip = None         # the one remote machine, that "currently" sends.


ending = False
while True:
  inputs = [proxy.udp_frontend_port, proxy.udp_backend_port]

  try:
    inputready,outputready,exceptready = select.select(inputs, [], [])
  except select.error as e:
    print("select.error", e)
    break
  except socket.error as e:
    print("socket.error", e)
    break

  if proxy.udp_backend_port in inputready:
    # laser is speaking
    data, addr = proxy.udp_backend_port.recvfrom(proxy.CHUNK_SZ)
    now = time.time()
    if last_client_ip is not None and addr[0] == ruida.dest:
      proxy.udp_frontend_port.sendto(data, (last_client_ip, proxy.CLIENT_PORT))       # forward what laser replies to client ...
      if ending:
        print("laser replied after FIN_TOKEN")
        last_client_ip = None
    else:
      if last_client_ip is None:
        print("sending NACK to laser, no connected client known.")
      else:
        print("sending NACK to unknon 'laser'. Go away,", addr)
      proxy.udp_backend_port.sendto(proxy.NACK_TOKEN, addr)       # we don't know where to route this...

  elif proxy.udp_frontend_port in inputready:
    data, addr = proxy.udp_frontend_port.recvfrom(proxy.CHUNK_SZ)
    if now - last_pkg_tstamp > BUSY_TIMEOUT:
      if last_client_ip != None:
        print("long pause. Disconnecting", last_client_ip)
        last_client_ip = None

    # a new client is talking to us
    if last_client_ip is None:
      last_client_ip = addr[0]

    if addr[0] == last_client_ip:
      # yes, please go ahead
      last_pkg_tstamp = now
      proxy.udp_backend_port.sendto(data, (proxy.dest, proxy.RUIDA_PORT))             # forward what client says to laser ...
      if data == proxy.FIN_TOKEN:
        print("FIN_TOKEN seen from client")
        ending = True
      else:
        ending = False
    else:
      print("who are you, ", addr, "? -- go away, we are busy with ", last_client_ip)
      proxy.udp_frontend_port.sendto(proxy.NACK_TOKEN, addr)       # you shall not pass.

  else:
    # select timeout?
    print(".", end="")
    if now - last_pkg_tstamp > BUSY_TIMEOUT:
      if last_client_ip != None:
        print("long pause. Disconnecting", last_client_ip)
        last_client_ip = None

