#! /usr/bin/python3
#
# (c) 2017 Patrick Himmelmann et.al.
# 2017-05-21
#
# (c) 2017-11-24, juergen@fabmail.org
#
# The code is fully compatible with python 2.7 and 3.5
#
# High level methods:
#  set(paths=[[..]], speed=.., power=[..], ...)
#  write(fd)
#
# Intermediate methods:
#  header(), body(), trailer()
#
# Low level methods:
#  encode_hex(), encode_relcoord(), encode_percent()
#  encode_number() for e.g.: # Bottom_Right_E7_51 452.84mm 126.8mm           e7 51 00 00 1b 51 68 00 00 07 5e 50
#  scramble()
#
# Some, but not all unscramble() decode_..() methods are also included.
# A self test example (cutting the triange in a square) is included at the end.
#
# 2017-12-03, jw@fabmail.org
#     v1.0 -- The test code produces a valid square_tri_test.rd, according to
#             githb.com/kkaempf/rudida/bin/decode

import sys, re

# python2 has a completely useless alias bytes = str. Fix this:
if sys.version_info.major < 3:
        def bytes(tupl):
                "Minimalistic python3 compatible implementation used in python2."
                return "".join(map(chr, tupl))


class Ruida():
  """
   Assemble a valid *.rd file from the following parameters:

   paths = [
            [[0,0], [50,0], [50,50], [0,50], [0,0]],
            [[12,10], [38,25], [12,40], [12,10]]
           ]
        This example is a 50 mm square, with a 30 mm triangle inside.

   speed = 30
   speed = [ 1000, 30 ]
        Movement speed in mm/sec.
        Can be scalar or sequence. A scalar NUMBER is the same as a
        sequence of [1000, NUMBER]. The first value of the sequence is
        used for travelling with lasers off.
        The second value is with laser1 on.

   power = [ 50, 70 ]
        Values in percent. The first value is the minimum power used near
        corners or start and end of lines.
        The second value is the maximum power used in the middle of long
        straight lines, this compensates for accellerated machine
        movements.  Additional pairs can be specified for a second, third,
        and fourth laser.

   bbox = [[0,0], [50,50]]
        Must span the rectangle that contains all points in the paths.
        Can also be ommited and/or computed by the boundingbox() method.
        The first point ([xmin, ymin] aka "top left") of the bounding
        box is ususally [0,0] so that the start position can be easily
        adjusted at the machine.
  """

  __version__ = "1.0"

  def __init__(self, paths=None, speed=None, power=None, bbox=None, freq=20.0):
    self._paths = paths

    self._bbox = bbox
    self._speed = speed
    self._power = power
    self._freq = freq

    self._header = None
    self._body = None
    self._trailer = None

  def set(self, paths=None, speed=None, power=None, bbox=None, freq=None):
    if paths is not None: self._paths = paths
    if speed is not None: self._speed = speed
    if power is not None: self._power = power
    if bbox  is not None: self._bbox  = bbox
    if freq  is not None: self._freq  = freq

  def write(self, fd, scramble=True):
    """
    Write a fully prepared object into a file (or raise ValueError()s
    for missing attributes). The object must be prepared by passing
    parameters to __init__ or set().

    The filedescriptor should be opened in "wb" mode.

    The file format is normally scrambled. Files written with
    scramble=False are not understood by the machine, but may be
    helpful for debugging.
    """

    if not self._header:
      if not self._freq: self._freq = 20.0    # kHz   (unused?)
      if not self._bbox and self._paths: self._bbox = self.boundingbox(self._paths)
      if self._bbox and self._speed and self._power and self._freq:
        self._header = self.header(self._bbox, self._speed, self._power, self._freq)
    if not self._body:
      if self._paths:
        self._body = self.body(self._paths)
    if not self._trailer: self._trailer = self.trailer()

    if not self._header:  raise ValueError("header(_bbox,_speed,_power,_freq) not initialized")
    if not self._body:    raise ValueError("body(_paths) not initialized")
    if not self._trailer: raise ValueError("trailer() not initialized")

    contents = self._header + self._body + self._trailer
    if scramble: contents = self.scramble_bytes(contents)
    fd.write(contents)

  def boundingbox(self, paths=None):
    """
    Returns a list of two pairs [xmin, ymin], [xmax, ymax]]
    that spans the rectangle containing all points found in paths.
    If no parameter is given, the _paths of the object are examined.
    """
    if paths is None: paths = self._paths
    if paths is None: raise ValueError("no paths")
    xmin = xmax = paths[0][0][0]
    ymin = ymax = paths[0][0][1]
    for path in paths:
      for point in path:
        if point[0] > xmax: xmax = point[0]
        if point[0] < xmin: xmin = point[0]
        if point[1] > ymax: ymax = point[1]
        if point[1] < ymin: ymin = point[1]
    return [[xmin, ymin], [xmax, ymax]]

  def body(self, paths, maxrel=-5.0):
    """
    Convert a set of paths into lasercut instructions.
    Returns the binary instruction data.

    maxrel is the limit in mm, for relative moves and cuts.
    The theoretical limit is assumed to be between 5 and 10 mm,

    FIXME: As of 2017-12-04 the encoding of enc('r', ...) is broken.
           We always use absolute moves and cuts.
    """

    def relok(last, point, maxrel):
      """
      Determine, if we can emit a relative move or cut command.
      An absolute move or cut costs 11 bytes,
      a relative one costs 5 bytes.
      """
      if last is None: return False
      dx = abs(point[0]-last[0])
      dy = abs(point[1]-last[1])
      return max(dx, dy) <= maxrel

    data = bytes([])

    lp = None
    for path in paths:
      travel = True
      for p in path:
        if relok(lp, p, maxrel):

          if travel:
            data += self.enc('-rr', ['89', p[0]-lp[0], p[1]-lp[1]])   # Move_To_Rel 3.091mm 0.025mm
          else:
            data += self.enc('-rr', ['a9', p[0]-lp[0], p[1]-lp[1]])   # Cut_Rel 0.015mm -1.127mm

        else:

          if travel:
            data += self.enc('-nn', ['88', p[0], p[1]])               # Move_To_Abs 0.0mm 0.0mm
          else:
            data += self.enc('-nn', ['a8', p[0], p[1]])               # Cut_Abs_a8 17.415mm 7.521mm

        lp = p
        travel = False
    return data

  def scramble_bytes(self, data):
    if sys.version_info.major < 3:
      return bytes([self.scramble(ord(b)) for b in data])
    else:
      return bytes([self.scramble(b) for b in data])

  def unscramble_bytes(self, data):
    if sys.version_info.major < 3:
      return bytes([self.unscramble(ord(b)) for b in data])
    else:
      return bytes([self.unscramble(b) for b in data])

  def unscramble(self, b):
    """ unscramble a single byte for reading from *.rd files """
    res_b=b-1
    if res_b<0: res_b+=0x100
    res_b^=0x88
    fb=res_b&0x80
    lb=res_b&1
    res_b=res_b-fb-lb
    res_b|=lb<<7
    res_b|=fb>>7
    return res_b

  def scramble(self, b):
    """ scramble a single byte for writing into *.rd files """
    fb=b&0x80
    lb=b&1
    res_b=b-fb-lb
    res_b|=lb<<7
    res_b|=fb>>7
    res_b^=0x88
    res_b+=1
    if res_b>0xff:res_b-=0x100
    return res_b

  def header(self, bbox, speed, power, freq):
    """
    Generate machine initialization instructions, to be sent before geometry.

    The bounding box bbox is expected in
    [[xmin, ymin], [xmax, ymax]] format, as returned by the boundingbox()
    method. Note: all test data seen had xmin=0, ymin=0.

    The power is expected as list of 2 to 8 elements, [min1, max1, ...]
    missing elements are added by repetition.
    Only one layer is currently initialized and used for all data.

    Units: Lengths in mm, power in percent [0..100],
           speed in mm/sec, freq in khz.

    Returns the binary instruction data.
    """

    if len(power) % 2: raise ValueError("Even number of elements needed in power[]")
    while len(power) < 8: power += power[-2:]
    (xmin, ymin) = bbox[0]
    (xmax, ymax) = bbox[1]

    if type(speed) == float or type(speed) == int: speed = [1000, speed]
    travelspeed = speed[0]
    laser1speed = speed[1]

    data = self.encode_hex("""
        d8 12           # Red Light on ?
        f0 f1 02 00     # file type ?
        d8 00           # Green Light off ?
        """)
    data += self.enc('-nn', ["e7 06", 0, 0])              # Feeding
    data += self.enc('-nn', ["e7 03", xmin, ymin])        # Top_Left_E7_07
    data += self.enc('-nn', ["e7 07", xmax, ymax])        # Bottom_Right_E7_07
    data += self.enc('-nn', ["e7 50", xmin, ymin])        # Top_Left_E7_50
    data += self.enc('-nn', ["e7 51", xmax, ymax])        # Bottom_Right_E7_51
    data += self.enc('-nn', ["e7 04 00 01 00 01", 0, 0])  # E7 04 ???
    data += self.enc('-n',  ["e7 05 00 c9 04 00", laser1speed]) # Speed_E7_05

    data += self.enc('-p-p', ["c6 31 00", power[0], "c6 32 00", power[1]]) # Laser_1_Min/Max_Pow Layer:0
    data += self.enc('-p-p', ["c6 41 00", power[2], "c6 42 00", power[3]]) # Laser_2_Min/Max_Pow Layer:0
    data += self.enc('-p-p', ["c6 35 00", power[4], "c6 36 00", power[5]]) # Laser_3_Min/Max_Pow Layer:0
    data += self.enc('-p-p', ["c6 37 00", power[6], "c6 38 00", power[7]]) # Laser_3_Min/Max_Pow Layer:0
    data += self.enc('-nn-nn-nn-nn-', ["""
        ca 06 00 00 00 00 00 00         # Layer_CA_06 Layer:0 00 00 00 00 00
        ca 41 00 00                     # ??
        e7 52 00""", xmin, ymin, """    # E7 52 Layer:0 top left?
        e7 53 00""", xmax, xmin, """    # Bottom_Right_E7_53 Layer:0
        e7 61 00""", xmin, ymin, """    # E7 61 Layer:0 top left?
        e7 62 00""", xmax, ymax, """    # Bottom_Right_E7_62 Layer:0
        ca 22 00                        # ??
        e7 54 00 00 00 00 00 00         # Pen_Draw_Y 00 0.0mm
        e7 54 01 00 00 00 00 00         # Pen_Draw_Y 01 0.0mm
        """])
    data += self.enc('-nn-nn-nn-nn-nn-nn-nn-nn-', ["""
        e7 55 00 00 00 00 00 00                         # Laser2_Y_Offset False 0.0mm
        e7 55 01 00 00 00 00 00                         # Laser2_Y_Offset True 0.0mm
        f1 03 00 00 00 00 00 00 00 00 00 00             # Laser2_Offset 0.0mm 0.0mm
        f1 00 00                                        # Start0 00
        f1 01 00                                        # Start1 00
        f2 00 00                                        # F2 00 00
        f2 01 00                                        # F2 01 00
        f2 02 05 2a 39 1c 41 04 6a 15 08 20             # F2 02 05 2a 39 1c 41 04 6a 15 08 20
        f2 03 """, xmin, ymin, """                      # F2 03 0.0mm 0.0mm
        f2 04 """, xmax, ymax, """                      # Bottom_Right_F2_04 17.414mm 24.868mm
        f2 06 """, xmin, ymin, """                      # F2 06 0.0mm 0.0mm
        f2 07 00                                        # F2 07 00
        f2 05 00 01 00 01 """, xmax, ymax, """          # Bottom_Right_F2_05 00 01 00 01 17.414mm 24.868mm
        ea 00                                           # EA 00
        e7 60 00                                        # E7 60 00
        e7 13 """, xmin, ymin, """                      # E7 13 0.0mm 0.0mm
        e7 17 """, xmax, ymax, """                      # Bottom_Right_E7_17 17.414mm 24.868mm
        e7 23 """, xmin, ymin, """                      # E7 23 0.0mm 0.0mm
        e7 24 00                                        # E7 24 00
        e7 08 00 01 00 01 """, xmax, ymax, """          # Bottom_Right_E7_08 00 01 00 01 17.414mm 24.868mm
        ca 01 00                                        # Flags_CA_01 00
        ca 02 00                                        # CA 02 Layer:0
        ca 01 30                                        # Flags_CA_01 30
        ca 01 10                                        # Flags_CA_01 10
        ca 01 13                                        # Blow_on
        """])
    data += self.enc('-n-p-p-p-p-p-p-p-p-p-p-p-p-', ["""
        c9 02 """, laser1speed, """     # Speed_C9 30.0mm/s
        c6 12 00 00 00 00 00            # Cut_Open_delay_12 0.0 ms
        c6 13 00 00 00 00 00            # Cut_Close_delay_13 0.0 ms
        c6 50 """, 100, """             # Cut_through_power1 100%
        c6 51 """, 100, """             # Cut_through_power2 100%
        c6 55 """, 100, """             # Cut_through_power3 100%
        c6 56 """, 100, """             # Cut_through_power4 100%
        c6 01 """, power[0], """        # Laser_1_Min_Pow_C6_01 0%
        c6 02 """, power[1], """        # Laser_1_Max_Pow_C6_02 0%
        c6 21 """, power[2], """        # Laser_2_Min_Pow_C6_21 0%
        c6 22 """, power[3], """        # Laser_2_Max_Pow_C6_22 0%
        c6 05 """, power[4], """        # Laser_3_Min_Pow_C6_05 1%
        c6 06 """, power[5], """        # Laser_3_Max_Pow_C6_06 0%
        c6 07 """, power[6], """        # Laser_4_Min_Pow_C6_07 0%
        c6 08 """, power[7], """        # Laser_4_Max_Pow_C6_08 0%
        ca 03 0f                        # Layer_CA_03 0f
        ca 10 00                        # CA 10 00
        """])
    return data


  def trailer(self, l=0.092):
    """
    Generate machine trailer instructions. To be sent after geometry instructions.

    Initialize a trailer with default Sew_Comp_Half length of 0.092 mm.
    Whatever that means.

    Returns the binary instruction data.
    """
    data = self.enc("-nn-", ["""
        eb e7 00
        da 01 06 20""", l, l, """
        d7 """])
    return data


  def encode_number(self, num, length=5, scale=1000):
    """
    The number n is expected in floating point format with unit mm.
    A bytes() array of size length is returned.
    The default scale converts to micrometers.
    length=5 and scale=1000 are the expected machine format.
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

  def enc(self, fmt, tupl):
    """
    Encode the elements of tupl according to the format string.
    Each character in fmt consumes the corresponds element from tupl
    as a parameter to an encoding method:
    '-'       encode_hex()
    'n'       encode_number()
    'p'       encode_percent()
    'r'       encode_relcoord()
    """
    if len(fmt) != len(tupl): raise ValueError("format '"+fmt+"' length differs from len(tupl)="+str(len(tupl)))

    ret = b''
    for i in range(len(fmt)):
      if   fmt[i] == '-': ret += self.encode_hex(tupl[i])
      elif fmt[i] == 'n': ret += self.encode_number(tupl[i])
      elif fmt[i] == 'p': ret += self.encode_percent(tupl[i])
      elif fmt[i] == 'r': ret += self.encode_relcoord(tupl[i])
      else: raise ValueError("unknown character in fmt: "+fmt)
    return ret

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
    Relative position in mm;
    Returns a bytes array of two elements.

    FIXME: As of 2017-12-04 this encoding is broken. Do not use.
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

  def encode_hex(self, str):
    """
    Assemble a string from hexadecimal digits. Binary safe.
    Example: "48 65 6c 6c f8  # with a smorrebrod o\n    21" -> b'Hell\xf7!'
    """
    str = re.sub('#.*$','', str, flags=re.MULTILINE)    # weed out comments.
    l = map(lambda x: int(x, base=16), str.split())     # locale.atoi() is to be avoided!
    return bytes(l)

if __name__ == '__main__':
  def hexdumpb(data):
    "Convenience hexdumper for bytes (or str), compatible with both python2 and python3"
    return ["%02x"%(ord(b) if type(b) == str else b) for b in data]

  rd = Ruida()
  data = b'\xe7\x51' + rd.encode_number(452.84) + rd.encode_number(126.8)
  print("Bottom_Right_E7_51 452.84mm 126.8mm          e7 51 00 00 1b 51 68 00 00 07 5e 50 ")
  print("Bottom_Right_E7_51 452.84mm 126.8mm          "+" ".join(hexdumpb(data)))

  data = b'\xa9' + rd.encode_relcoord(-0.982) + rd.encode_relcoord(0.011)
  print("Cut_Rel -0.982mm 0.011mm                     a9 78 55 00 16")
  print("Cut_Rel -0.982mm 0.011mm                     "+" ".join(hexdumpb(data)))

  data = b'\xa9' + rd.encode_relcoord(-0.075) + rd.encode_relcoord(0.917)
  print("Cut_Rel -0.075mm 0.917mm                     a9 7f 6a 07 2b")
  print("Cut_Rel -0.075mm 0.917mm                     "+" ".join(hexdumpb(data)))

  data = b'\xc6\x31\x00' + rd.encode_percent(60)
  print("Laser_1_Min_Pow_C6_31 Layer:0 0%             c6 31 00 4c 65")
  print("Laser_1_Min_Pow_C6_31 Layer:0 0%             "+" ".join(hexdumpb(data)))

  data = b'\xc6\x32\x00' + rd.encode_percent(70)
  print("Laser_1_Max_Pow_C6_32 Layer:0 0%             c6 32 00 59 4c")
  print("Laser_1_Max_Pow_C6_32 Layer:0 0%             "+" ".join(hexdumpb(data)))





  rd = Ruida()
  # rd.set(speed=30, power=[40,70])             # cut 4mm plywood
  rd.set(speed=100, power=[10,15])              # mark
  rd.set(paths=[
        [[0,0], [50,0], [50,50], [0,50], [0,0]],
#        [[12,10], [38,25], [12,40], [12,10]],
#        [[16,6], [10,6], [13,3], [16, 6]]
        [[12,10], [38,25], [12,40], [12,11]],
        [[15,6], [10,6], [13,3], [16, 6]]
      ])

  with open('square_tri_test.rd', 'wb') as fd:
    rd.write(fd)

