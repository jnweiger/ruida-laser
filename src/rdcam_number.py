#! /usr/bin/python3
#
# (c) 2017 Patrick Himmelmann et.al.
# 2017-05-21
#
# (c) 2017-11-24, juergen@fabmail.org
#
# encode_numbers for e.g.:
# Bottom_Right_E7_51 452.84mm 126.8mm           e7 51 00 00 1b 51 68 00 00 07 5e 50
# encode_relcoord, encode_percent

import sys

# python2 has a completely useless alias bytes = str. Fix this:
if sys.version_info.major < 3:
        def bytes(tupl):
                return "".join(map(chr, tupl))
        def hexbytes(data):
                return ["%02x"%(ord(b) if type(b) == str else b) for b in data]
else:
        def hexbytes(data):
                return ["%02x"%b for b in data]

class Ruida:
  def encode_number(self, num, length=5, scale=1000):
    """
    The number n is expected in floating point format with unit mm.
    A bytes() array of size length is returned scaled up (to micrometers with scale=1000).
    """
    res = []
    nn = int(num * scale)
    while nn > 0:
        res.append(nn & 0x7f)
        nn >>= 7
    while len(res) < length:
        res.append(0)
    res.reverse()
    return bytes(res)

  def decode_number(self, x):
    "used with a bytes() array of length 5"
    fak=1
    res=0
    for b in reversed(x):
        res+=fak*b
        fak*=0x80
    return 0.0001 * res

  def encode_relcoord(self, n):
      """
      relative position in mm;
      Returns a bytes array of two elements.
      """
      nn = int(n*1000)
      if nn > 8192 or nn < -8191:
          raise ValueError("relcoord "+str(n)+" mm is out of range. Use abscoords!")
      if nn < 0: nn += 16384
      nn <<= 1
      return bytes([nn>>8, nn&0xff])    # 8-bit encoding with lost lsb.

  def decode_relcoord(self, x):
      """
      using the first two elements of array x
      relative position in micrometer; signed (2s complement)
      """
      r = x[0] << 8
      r += x[1]
      r >>= 1
      if r > 16383 or r < 0:
        raise ValueError("Not a rel coord: " + repr(x[0:2]))
      if r > 8192: return 0.001 * (r-16384)
      else:        return 0.001 * r

  def encode_percent(self, n):
      """
      returns two bytes, used with laser and layer percentages.
      The magic constant 163.83 is 1/100 of 14bit all 1s.
      """
      a = int(n*0x3fff*0.01)    # n * 163.83
      return bytes([a>>7, a&0x7f])      # 7-bit encoding


if __name__ == '__main__':
    rd = Ruida()
    data = b'\xe7\x51' + rd.encode_number(452.84) + rd.encode_number(126.8)
    print("Bottom_Right_E7_51 452.84mm 126.8mm           e7 51 00 00 1b 51 68 00 00 07 5e 50 ")
    print("Bottom_Right_E7_51 452.84mm 126.8mm           "+" ".join(hexbytes(data)))

    data = b'\xa9' + rd.encode_relcoord(-0.982) + rd.encode_relcoord(0.011)
    print("Cut_Rel -0.982mm 0.011mm                        a9 78 55 00 16")
    print("Cut_Rel -0.982mm 0.011mm                        "+" ".join(hexbytes(data)))

    data = b'\xa9' + rd.encode_relcoord(-0.075) + rd.encode_relcoord(0.917)
    print("Cut_Rel -0.075mm 0.917mm                        a9 7f 6a 07 2b")
    print("Cut_Rel -0.075mm 0.917mm                        "+" ".join(hexbytes(data)))

    data = b'\xc6\x31\x00' + rd.encode_percent(60)
    print("Laser_1_Min_Pow_C6_31 Layer:0 0%		c6 31 00 4c 65")
    print("Laser_1_Min_Pow_C6_31 Layer:0 0%		"+" ".join(hexbytes(data)))

    data = b'\xc6\x32\x00' + rd.encode_percent(70)
    print("Laser_1_Max_Pow_C6_32 Layer:0 0%		c6 32 00 59 4c")
    print("Laser_1_Max_Pow_C6_32 Layer:0 0%		"+" ".join(hexbytes(data)))
