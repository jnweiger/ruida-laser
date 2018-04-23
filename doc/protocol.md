(Seen in https://wiki.fablab-nuernberg.de/index.php?title=Diskussion:Nova_35&action=edit)

=== Data format ===

* Byte = 1 Bit Message Start Indicator + 7 Bit Payload
* Only one message (checksum + command) can be sent per UDP package
* Max UDP package size 1472 bytes including checksum; fragmented by simple cutting (even inside a command)

==== Checksum ====

2 Bytes - sum of scrambled message bytes; MSB first.
Checksum has to be send before message.

==== UDP Transmission ====

* The device listens on a fixed UDP port 50200. IPaddress is configurable, but netmask is 255.255.255.0 fixed.
* An RD file is transfered as payload, same commands and syntax as with USB-Serial or USB-MassStorage.
* The payload is split in chunks with a well known maximum size (MTU). (The last packet is usually shorter)
* There is no header, and no arbitration phase, but successful transmission of the first chunk indicates device ready.
* Each chunk starts with a two byte checksum, followed by payload data. Length of the payload is implicit by the
  UDP datagram size. (Would not work with TCP)
* Each chunk is acknowledged with a single byte response packet:
  0xc6 if all is well, The next chunk should be sent. TODO: Within a timout?
  0x46 if error. TODO: Checksum error and/or busy?
* The first chunk should be retried when 0x46 was received. For subsequent chunks transmission should be aborted.

==== Values ====

{| class="wikitable sortable"
|-
! Value !! Lenght !! Description
|-
|id="VAL-ABSCOORD"| ABSCOORD || 5 Bytes || absolute position relative to job origin in µm
|-
|id="VAL-RELCOORD"| RELCOORD || 2 Bytes || relative position in µm; signed (2s complement)
|-
|id="VAL-SPEED"| SPEED || 5 Bytes || speed in µm/s
|-
|id="VAL-POWER"| POWER || 2 Bytes || power in 0,006103516% (100/2^14)
|-
|id="VAL-CSTRING"| CSTRING || variable zero terminated || 
|}

==== Commands ====

{| class="wikitable sortable"
|-
! Byte squence !! Description !! how sure we are
|-
| C6 01 [[#VAL-POWER|<POWER>]] || 1st laser source min power || 99%
|-
| C6 21 [[#VAL-POWER|<POWER>]] || 2nd laser source min power || 99%
|-
| C6 02 [[#VAL-POWER|<POWER>]] || 1st laser source max power || 99%
|-
| C6 22 [[#VAL-POWER|<POWER>]] || 2nd laser source max power || 99%
|-
| C9 02 [[#VAL-SPEED|<SPEED>]] || movement and/or (not sure) cutting speed || 80%
|-
| D9 00 02 [[#VAL-ABSCOORD|<ABSCOORD>]] || move X || 99%
|-
| D9 00 03 [[#VAL-ABSCOORD|<ABSCOORD>]] || move Y || 50%
|-
| D9 00 04 [[#VAL-ABSCOORD|<ABSCOORD>]] || move Z || 50%
|-
| D9 00 05 [[#VAL-ABSCOORD|<ABSCOORD>]] || move U || 50%
|-
| CC || ACK from machine || 99%
|-
| CD || ERR from machine || 99%
|-
| DA 00 XX XX || get XX XX from machine || 99%
|-
| DA 00 04 05 || saved job count || 99%
|-
| DA 01 XX XX <VALUE> || response to DA 00 XX XX || 99%
|-
| A8 [[#VAL-ABSCOORD|<ABSCOORD>]] [[#VAL-ABSCOORD|<ABSCOORD>]] || Straight cut to absolute X Y; turn laser on with configured speed and power || 99%
|-
| A9 [[#VAL-RELCOORD|<RELCOORD>]] [[#VAL-RELCOORD|<RELCOORD>]] || Straight cut to relative X Y; turn laser on with configured speed and power || 99%
|-
| E7 50 [[#VAL-ABSCOORD|<ABSCOORD>]] [[#VAL-ABSCOORD|<ABSCOORD>]] || Bounding box top left? || 30%
|-
| E7 51 [[#VAL-ABSCOORD|<ABSCOORD>]] [[#VAL-ABSCOORD|<ABSCOORD>]] || Bounding box bottom right? || 30% 
|-
| E8 02 E7 01 [[#VAL-CSTRING|<CSTRING>]] || Set filename for following transfer (transfer needs to be done really quickly after this!) || 90%
|-
| E8 01 XX XX || Read filename number XX XX ||
|-
| 88 [[#VAL-ABSCOORD|<ABSCOORD>]] [[#VAL-ABSCOORD|<ABSCOORD>]] || straight move to absolute X Y as fast as possible; with laser off || 99%
|-
| 89 [[#VAL-RELCOORD|<RELCOORD>]] [[#VAL-RELCOORD|<RELCOORD>]] || straight move to relative X Y as fast as possible; with laser off || 80%
|}

