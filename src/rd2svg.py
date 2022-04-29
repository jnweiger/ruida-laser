#! /usr/bin/python3
#
# rd2svg.py
#
# Requires:
#  sudo pip3 install svg.py
#  sudo pip3 install typing_extensions
#
# 2022-02-06, v0.1, jw:       Initial draught: can tokenize square_tri_test.rd
# 2022-02-07, v0.2, jw:       Commands added, parameter decoding wip.
# 2022-02-08, v0.3, jw:       Add layer info to paths.
# 2022-02-08, v1.0, jw:       Can convert square_tri_test.rd into a nice svg.
#
import sys
from ruidaparser import RuidaParser

r = RuidaParser(file=sys.argv[1])
r.decode(debug=True)
print(r.to_svg())

if False:
  from pprint import pprint
  pprint({ 'p':r._paths, 'bbox':r._bbox, 'las':r._laser}, depth=5, stream=sys.stderr)

###

