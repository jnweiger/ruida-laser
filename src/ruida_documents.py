#! /usr/bin/python3
#
#0xE8 	0x00 		0xE8 0x00 	            12 	Delete Document
#0xE8 	0x01 		0xE8 0x01 <FileNumber> 	4 	Document Name <FileNumber>
#0xE8 	0x02 		0xE8 0x02 	            2 	File Transfer
#0xE8 	0x03 		0xE8 0x03 <Index> 	    3 	Select Document <Index>
#0xE8 	0x04 		0xE8 0x04 	            2 	Calculate Document Time 

from ruida import Ruida, RuidaUdp

host="
if len(sys.argv) < 2:
  print("Usage: %s IPADDR FILE.rd" % sys.argv[0])
host=sys.argv[1]

rd = Ruida()

print(rd)
