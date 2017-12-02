#! /usr/bin/python3
#
# (c) 2017 Patrick Himmelmann et.al.
# 2017-05-21
#
# (c) 2017-11-24, juergen@fabmail.org
#
# encode numbers for e.g.:
# Bottom_Right_E7_51 452.84mm 126.8mm           e7 51 00 00 1b 51 68 00 00 07 5e 50 

import sys

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

  def decode_relcoord(self, x):
      """
      using the first two elements of array x
      relative position in µm; signed (2s complement)
      """
      r = x[0] << 8
      r += x[1]
      r >>= 1
      if r > 16383 or r < 0:
        raise "Not a rel coord"
      if r > 8182: return 0.001 * (r-16384)
      else:        return 0.001 * r

  def encode_percent(self, n):
      """
      returns two bytes, used with laser and layer percentages.
      The magic constant 163.83 is 1/100 of 14bit all 1s.
      """
      a = int(n*0x3fff*0.01)    # n* 163.83
      return bytes([a>>7], [a&0x7f])


 __name__ == '__main__':
    rd = Ruida()
    data = b'\xe7\x51' + rd.encode_number(452.84) + rd.encode_number(126.8)
    print("Bottom_Right_E7_51 452.84mm 126.8mm           e7 51 00 00 1b 51 68 00 00 07 5e 50 ")
    print("Bottom_Right_E7_51 452.84mm 126.8mm           "+" ".join(["%02x"%b for b in data]))

    data = b'\xa9' + rd.encode_num2(-0.982) + rd.encode_num2(0.011)
    print("Cut_Rel -0.982mm 0.011mm                        a9 78 55 00 16")
    print("Cut_Rel -0.982mm 0.011mm                        "+" ".join(["%02x"%b for b in data]))

    data = b'\xa9' + rd.encode_num2(-0.075) + rd.encode_num2(0.917)
    print("Cut_Rel -0.075mm 0.917mm                        a9 7f 6a 07 2b")
    print("Cut_Rel -0.075mm 0.917mm                        "+" ".join(["%02x"%b for b in data]))
