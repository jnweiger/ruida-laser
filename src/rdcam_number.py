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

  def encode_num5(self, num): return self.encode_number(num, 5, 1000)
  def encode_num2(self, num): return self.encode_number(num, 2, 2000)

  def decode_number(self, x):
    fak=1
    res=0
    for b in reversed(x):
        res+=fak*b
        fak*=0x80
    return 0.0001 * res


if __name__ == '__main__':
    rd = Ruida()
    data = b'\xe7\x51' + rd.encode_num5(452.84) + rd.encode_num5(126.8)
    print("Bottom_Right_E7_51 452.84mm 126.8mm           e7 51 00 00 1b 51 68 00 00 07 5e 50 ")
    print("Bottom_Right_E7_51 452.84mm 126.8mm           "+" ".join(["%02x"%b for b in data]))

    data = b'\xa9' + rd.encode_num2(-0.982) + rd.encode_num2(0.011)
    print("Cut_Rel -0.982mm 0.011mm                        a9 78 55 00 16")
    print("Cut_Rel -0.982mm 0.011mm                        "+" ".join(["%02x"%b for b in data]))

    data = b'\xa9' + rd.encode_num2(-0.075) + rd.encode_num2(0.917)
    print("Cut_Rel -0.075mm 0.917mm                        a9 7f 6a 07 2b")
    print("Cut_Rel -0.075mm 0.917mm                        "+" ".join(["%02x"%b for b in data]))
