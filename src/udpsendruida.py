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
#   0xc6 if all is well, The next chunk should be sent. A delay of 4 seconds was tested successfully.
#   0x46 if error. TODO: Checksum error and/or busy? A running laser job does not cause a busy condition.
# - The first chunk should be retried when 0x46 was received. For subsequent chunks transmission should be aborted.
# - No pause is needed after the last chunk. The payload contains a termination token.
#
# test against:
# ncat -l -u -v 50200

from ruida import RuidaUdp
import sys

if sys.version_info.major < 3:
  print("Need python3 for "+sys.argv[0])
  sys.exit(1)

if len(sys.argv) < 3:
  print("Usage: %s IPADDR FILE.rd" % sys.argv[0])
  sys.exit(1)

host=sys.argv[1]
file=sys.argv[2]


laser = RuidaUdp(host)
rdfile = open(file, 'rb').read()
laser.write(rdfile)
