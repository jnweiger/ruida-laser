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
# 2017-12-11, jw@fabmail.org
#     v1.2 -- Correct maxrel 8.191 found.
#             Implemented Cut_Horiz, Cut_Vert, Move_Horiz, Move_Vert
#             Updated encode_relcoord() to use encode_number(2)
# 2017-12-13, jw@fabmail.org
#     v1.3 -- added _forceabs = 100. Limit possible precision loss.
# 2017-12-14, jw@fabmail.org
#     v1.4 -- added bbox2moves() and paths2moves()
# 2017-12-16, jw@fabmail.org
#     v1.5 -- added interface to support multiple layer
# 2017-12-18, jw@fabmail.org
#     v1.6 -- encode_byte() encode_color() added.
#             multi layer support in header() and body() done.

import sys, re, math, copy

# python2 has a completely useless alias bytes = str. Fix this:
if sys.version_info.major < 3:
        def bytes(tupl):
                "Minimalistic python3 compatible implementation used in python2."
                return "".join(map(chr, tupl))

class RuidaLayer():
  """
  """
  def __init__(self, paths=None, speed=None, power=None, bbox=None, color=[0,0,0], freq=20.0):
    self._paths = paths

    self._bbox  = bbox
    self._speed = speed
    self._power = power
    self._color = color
    self._freq  = freq

  def set(self, paths=None, speed=None, power=None, bbox=None, color=None, freq=None):
    if paths is not None: self._paths = paths
    if speed is not None: self._speed = speed
    if power is not None: self._power = power
    if bbox  is not None: self._bbox  = bbox
    if color is not None: self._color = color
    if freq  is not None: self._freq  = freq



class Ruida():
  """
   Assemble a valid *.rd file with multiple layers. Each layer has the following parameters:

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

   color = [0,255,0]
        Give a display color for the layer. This is used in the preview
        to visualize different layers in different colors.
        Expected as a triple [RED, GREEN, BLUE] each in [0..255]
  """

  __version__ = "1.6"

  def __init__(self, layers=None):
    if layers is None: layers = []
    self._layers = layers

    self._odo = None

    self._header = None
    self._body = None
    self._trailer = None

    # Must do an absolute mov/cut every now and then to avoid precision loss.
    # Worst case estimation: A deviation of 0.1mm is acceptable, this is circa the
    # diameter of the laser beam. Precision loss can occur due to rounding of the last decimal,
    # Which can contribute less than 0.001 mm each time. Thus a helpful value should be around
    # 100. We want the value as high as possible to safe code size, but slow enough to keep the
    # precision loss invisible.
    #
    # Set to 1, to disable relative moves.
    # Set to 0, to never force an absolute move. Allows potentially infinite precision loss.
    self._forceabs = 100

  def addLayer(self, layer):
    self._layers.append(layer)

  def set(self, nlayers=None, layer=0, paths=None, speed=None, power=None, bbox=None, freq=None, odo=None, color=None, forceabs=None):
    if forceabs is not None: self._forceabs = forceabs
    if bbox     is not None: self._bbox     = bbox
    if odo      is not None: self._odo      = odo

    if layer >= len(self._layers): nlayers = layer+1

    if nlayers  is not None:
      if nlayers < len(self._layers): self._layers = self._layers[0:nlayers]
      while nlayers > len(self._layers): self.addLayer(RuidaLayer())

    if paths is not None: self._layers[layer].set(paths = paths)
    if speed is not None: self._layers[layer].set(speed = speed)
    if power is not None: self._layers[layer].set(power = power)
    if bbox  is not None: self._layers[layer].set(bbox  = bbox)
    if freq  is not None: self._layers[layer].set(freq  = freq)
    if color is not None: self._layers[layer].set(color = color)


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
      if self._layers:
        for l in self._layers:
          if l._bbox is None and l._paths: l._bbox = self.boundingbox(l._paths)
      self._header = self.header(self._layers)
    if not self._body:
      if self._layers:
        self._body = self.body(self._layers)
    if not self._odo:
      if self._layers:
        for l in self._layers:
          self.odoAdd(self.odometer(l._paths))
    if not self._trailer: self._trailer = self.trailer(self._odo)

    if not self._header:  raise ValueError("header(_bbox,_speed,_power,_freq) not initialized")
    if not self._body:    raise ValueError("body(_layers) not initialized")
    if not self._trailer: raise ValueError("trailer() not initialized")

    contents = self._header + self._body + self._trailer
    if scramble: contents = self.scramble_bytes(contents)
    fd.write(contents)

  def odometer(self, paths=None, init=[0,0], return_home=False):
    """
    Returns a list of two values: [ cut_distance, travel_distance ]
    Note that these distances are subject to path ordering.
    Call this after all optimizations.
    """
    if paths is None: paths = self._paths
    if paths is None: raise ValueError("no paths")

    def dist_xy(p1, p2):
      dx = p2[0] - p1[0]
      dy = p2[1] - p1[1]
      return math.sqrt(dx*dx+dy*dy)

    cut_d = 0
    trav_d = 0
    xy = init
    for path in paths:
      traveling=True
      for point in path:
        if traveling:
          trav_d += dist_xy(xy, point)
          xy = point
          traveling = False
        else:
          cut_d += dist_xy(xy, point)
          xy = point
    if return_home:
      trav_d += dist_xy(xy, init)
    return [ cut_d, trav_d ]

  def odoAdd(self, odo):
    if self._odo is None:
      self._odo = copy.copy(odo)        # we change values later. Thus we need a copy.
    else:
      for n in range(len(odo)):
        self._odo[n] += odo[n]

  def paths2moves(self, paths=None):
    """
    Returns a list of one-element-lists, each point in any of the
    sub-paths as a its own list. This is technique generates
    only move instructions in the rd output (laser inactive).
    """
    if paths is None: paths = self._paths
    if paths is None: raise ValueError("no paths")
    moves = []
    for path in paths:
      for point in path:
        moves.append([[point[0], point[1]]])
    return moves

  def boundingbox(self, paths=None):
    """
    Returns a list of two pairs [[xmin, ymin], [xmax, ymax]]
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

  def bbox_combine(self, bbox1, bbox2):
    """
    returns the boundingbox of two bounding boxes.
    """
    if bbox1 is None: return bbox2
    if bbox2 is None: return bbox1
    x0 = min(bbox1[0][0], bbox2[0][0])
    y0 = min(bbox1[0][1], bbox2[0][1])
    x1 = max(bbox1[1][0], bbox2[1][0])
    y1 = max(bbox1[1][1], bbox2[1][1])
    return [[x0, y0], [x1, y1]]

  def bbox2moves(self, bbox):
    """
    bbox = [[x0, y0], [x1, y1]]
    """
    x0 = bbox[0][0]
    y0 = bbox[0][1]
    x1 = bbox[1][0]
    y1 = bbox[1][1]
    return [[[x0,y0]], [[x1,y0]], [[x1,y1]], [[x0,y1]], [[x0, y0]]]

  def body(self, layers):
    """
    Convert a set of paths (one set per layer) into lasercut instructions.
    Each layer has a prolog, that directly sets speed and powers.

    Returns the binary instruction data.
    """

    def relok(last, point):
      """
      Determine, if we can emit a relative move or cut command.
      An absolute move or cut costs 11 bytes,
      a relative one costs 5 bytes.
      """
      maxrel = 8.191     # 8.191 encodes as 3f 7f. -8.191 encodes as 40 01

      if last is None: return False
      dx = abs(point[0]-last[0])
      dy = abs(point[1]-last[1])
      return max(dx, dy) <= maxrel

    data = bytes([])
    # for lnum in reversed(range(len(layers))):         # Can be permuted, lower lnum's are processed first. Always.
    for lnum in range(len(layers)):
      l = layers[lnum]

      # CAUTION: keep in sync with header()
      power = copy.copy(l._power)
      if len(power) % 2: raise ValueError("Even number of elements needed in power[]")
      while len(power) < 8: power += power[-2:]

      speed = copy.copy(l._speed)
      if type(speed) == float or type(speed) == int: speed = [1000, speed]
      travelspeed = speed[0]
      laserspeed = speed[1]

      ################## Body Prolog Start #######################
      data += self.enc('-b-', ["""
          ca 01 00                                        # Flags_CA_01 00
          ca 02""", lnum, """                             # CA 02 Layer:0 priority?
          ca 01 30                                        # Flags_CA_01 30
          ca 01 10                                        # Flags_CA_01 10
          ca 01 13                                        # Blow_on
          """])

      ##   '-p-p-p-p-'
      #    c6 12 00 00 00 00 00            # Cut_Open_delay_12 0.0 ms
      #    c6 13 00 00 00 00 00            # Cut_Close_delay_13 0.0 ms
      #    c6 50 """, 100, """             # Cut_through_power1 100%
      #    c6 51 """, 100, """             # Cut_through_power2 100%
      #    c6 55 """, 100, """             # Cut_through_power3 100%
      #    c6 56 """, 100, """             # Cut_through_power4 100%
      ## if the Cut_through_powers are not present, then c6 15 and c6 16 instead.

      data += self.enc('-n-p-p-p-p-p-p-p-p-', ["""
          c9 02 """, laserspeed, """      # Speed_C9 30.0mm/s
          c6 15 00 00 00 00 00            # Cut_Open_delay_12 0.0 ms
          c6 16 00 00 00 00 00            # Cut_Close_delay_13 0.0 ms
          c6 01 """, power[0], """        # Laser_1_Min_Pow_C6_01 0%
          c6 02 """, power[1], """        # Laser_1_Max_Pow_C6_02 0%
          c6 21 """, power[2], """        # Laser_2_Min_Pow_C6_21 0%
          c6 22 """, power[3], """        # Laser_2_Max_Pow_C6_22 0%
          c6 05 """, power[4], """        # Laser_3_Min_Pow_C6_05 1%
          c6 06 """, power[5], """        # Laser_3_Max_Pow_C6_06 0%
          c6 07 """, power[6], """        # Laser_4_Min_Pow_C6_07 0%
          c6 08 """, power[7], """        # Laser_4_Max_Pow_C6_08 0%
          ca 03 01                        # Layer_CA_03 01
          ca 10 00                        # CA 10 00
          """])
      ################## Body Prolog End #######################

      relcounter = 0
      lp = None
      for path in l._paths:
        travel = True
        for p in path:
          if relok(lp, p) and (self._forceabs == 0 or relcounter < self._forceabs):

            if self._forceabs > 0: relcounter += 1

            if p[1] == lp[1]:     # horizontal rel
              if travel:
                data += self.enc('-r', ['8a', p[0]-lp[0]])   # Move_Horiz 6.213mm
              else:
                data += self.enc('-r', ['aa', p[0]-lp[0]])   # Cut_Horiz -6.008mm
            elif p[0] == lp[0]:   # vertical rel
              if travel:
                data += self.enc('-r', ['8b', p[1]-lp[1]])   # Move_Vert 17.1mm
              else:
                data += self.enc('-r', ['ab', p[1]-lp[1]])   # Cut_Vert 2.987mm
            else:                 # other rel
              if travel:
                data += self.enc('-rr', ['89', p[0]-lp[0], p[1]-lp[1]])   # Move_To_Rel 3.091mm 0.025mm
              else:
                data += self.enc('-rr', ['a9', p[0]-lp[0], p[1]-lp[1]])   # Cut_Rel 0.015mm -1.127mm

          else:

            relcounter = 0

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

  def header(self, layers):
    """
    Generate machine initialization instructions, to be sent before geometry.

    layers is a list of RuidaLayer() objects, containing:

    _bbox in [[xmin, ymin], [xmax, ymax]] format, as returned by the boundingbox()
            method. Note: all test data seen had xmin=0, ymin=0.
    _speed: single value per layer.
    _power: a list of 2 to 8 elements, [min1, max1, ...]
            Missing elements are added by repetition.

    Units: Lengths in mm, power in percent [0..100],
            speed in mm/sec, freq in khz.

    Returns the binary instruction data.
    """

    bbox = None
    for l in layers:
      print("layer bbox: ", l._bbox)
      bbox = self.bbox_combine(bbox, l._bbox)
    print("combined: ", bbox)
    (xmin, ymin) = bbox[0]
    (xmax, ymax) = bbox[1]

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
    data += self.enc('-',   ["e7 05 00"])                 # E7 05 ???

    ## start of per layer headers

    for lnum in range(len(layers)):
      l = layers[lnum]

      # CAUTION: keep in sync with body()
      power = copy.copy(l._power)
      if len(power) % 2: raise ValueError("Even number of elements needed in power[]")
      while len(power) < 8: power += power[-2:]

      speed = copy.copy(l._speed)
      if type(speed) == float or type(speed) == int: speed = [1000, speed]
      travelspeed = speed[0]
      laserspeed = speed[1]

      data += self.enc('-bn',  ["c9 04", lnum, laserspeed])

      data += self.enc('-bp-bp', ["c6 31", lnum, power[0], "c6 32", lnum, power[1]]) # Laser_1_Min/Max_Pow
      data += self.enc('-bp-bp', ["c6 41", lnum, power[2], "c6 42", lnum, power[3]]) # Laser_2_Min/Max_Pow
      data += self.enc('-bp-bp', ["c6 35", lnum, power[4], "c6 36", lnum, power[5]]) # Laser_3_Min/Max_Pow
      data += self.enc('-bp-bp', ["c6 37", lnum, power[6], "c6 38", lnum, power[7]]) # Laser_3_Min/Max_Pow

      data += self.enc('-bc-bb-bnn-bnn-bnn-bnn-', ["""
        ca 06""", lnum, l._color, """                     # Layer_CA_06 Layer:0 00 00 00 00 00  RGB-Color for preview
        ca 41""", lnum, 0, """                            # ??
        e7 52""", lnum, l._bbox[0][0], l._bbox[0][1], """ # E7 52 Layer:0 top left?
        e7 53""", lnum, l._bbox[1][0], l._bbox[1][1], """ # Bottom_Right_E7_53 Layer:0
        e7 61""", lnum, l._bbox[0][0], l._bbox[0][1], """ # E7 61 Layer:0 top left?
        e7 62""", lnum, l._bbox[1][0], l._bbox[1][1], """ # Bottom_Right_E7_62 Layer:0
        """])

    ## end of per layer headers

    data += self.enc('-b-', ["""
        ca 22""", len(layers)-1, """    # ?? Max layer number ??
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
        """])
    return data


  def trailer(self, odo=[0.0, 0.0]):
    """
    Generate machine trailer instructions. To be sent after geometry instructions.

    Initialize a trailer with the cut distance in m, not mm.
    Note, that RDworks8 uses the cut distance twice here, and does not send the
    the travel distance. Is this a bug?

    Returns the binary instruction data.
    """
    data = self.enc("-nn-", ["""
        eb e7 00
        da 01 06 20""", odo[0]*0.001, odo[0]*0.001, """
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

  def encode_color(self, color):
    """
    color = [RED, GREEN, BLUE]
    """
    cc = ((color[2]&0xff)<<16) + ((color[1]&0xff)<<8) + (color[0]&0xff)
    return self.encode_number(cc, scale=1)

  def enc(self, fmt, tupl):
    """
    Encode the elements of tupl according to the format string.
    Each character in fmt consumes the corresponds element from tupl
    as a parameter to an encoding method:
    '-'       encode_hex()
    'n'       encode_number()
    'p'       encode_percent()
    'r'       encode_relcoord()
    'b'       encode_byte()
    'c'       encode_color()
    """
    if len(fmt) != len(tupl): raise ValueError("format '"+fmt+"' length differs from len(tupl)="+str(len(tupl)))

    ret = b''
    for i in range(len(fmt)):
      if   fmt[i] == '-': ret += self.encode_hex(tupl[i])
      elif fmt[i] == 'n': ret += self.encode_number(tupl[i])
      elif fmt[i] == 'p': ret += self.encode_percent(tupl[i])
      elif fmt[i] == 'r': ret += self.encode_relcoord(tupl[i])
      elif fmt[i] == 'b': ret += self.encode_byte(tupl[i])
      elif fmt[i] == 'c': ret += self.encode_color(tupl[i])
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
    """
    nn = int(n*1000)
    if nn > 8191 or nn < -8191:
      raise ValueError("relcoord "+str(n)+" mm is out of range. Use abscoords!")
    if nn < 0: nn += 16384
    return self.encode_number(nn, length=2, scale=1)

  def decode_relcoord(self, x):
    """
    using the first two elements of array x
    relative position in micrometer; signed (2s complement)
    """
    r = x[0] << 8
    r += x[1]
    if r > 16383 or r < 0:
      raise ValueError("Not a rel coord: " + repr(x[0:2]))
    if r > 8191: return 0.001 * (r-16384)
    else:        return 0.001 * r

  def encode_byte(self, n):
    return self.encode_number(n, length=1, scale=1)

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

  data = b'\xc6\x31\x00' + rd.encode_percent(60)
  print("Laser_1_Min_Pow_C6_31 Layer:0 0%             c6 31 00 4c 65")
  print("Laser_1_Min_Pow_C6_31 Layer:0 0%             "+" ".join(hexdumpb(data)))

  data = b'\xc6\x32\x00' + rd.encode_percent(70)
  print("Laser_1_Max_Pow_C6_32 Layer:0 0%             c6 32 00 59 4c")
  print("Laser_1_Max_Pow_C6_32 Layer:0 0%             "+" ".join(hexdumpb(data)))

  data = b'\xa9' + rd.encode_relcoord(-8.191) + rd.encode_relcoord(8.191)
  print("Cut_Rel -8.191mm 8.191mm                     a9 40 01 3f 7f")
  print("Cut_Rel -8.191mm 8.191mm                     "+" ".join(hexdumpb(data)))

  data = b'\x89' + rd.encode_relcoord(4.0) + rd.encode_relcoord(-4.0)
  print("Mov_Rel 4.0mm -4.0mm                         89 1f 20 60 60")
  print("Mov_Rel 4.0mm -4.0mm                         "+" ".join(hexdumpb(data)))


  rd = Ruida()
  # rd.set(speed=30, power=[40,70])             # cut 4mm plywood
  rd.set(speed=100, power=[10,15])              # mark
  paths=[
        [[0,0], [50,0], [50,50], [0,50], [0,0]],
        [[12,10], [38,25], [12,40], [12,10]],
        [[16,6], [10,6], [13,3], [16, 6]]
      ]
  mvpath = rd.paths2moves(paths)
  mvbbox = rd.bbox2moves(rd.boundingbox(paths))

  mvbbox_cmp = [
        [[0,0]], [[50,0]], [[50,50]], [[0,50]], [[0,0]],
      ]
  mvpath_cmp = [
        [[0,0]], [[50,0]], [[50,50]], [[0,50]], [[0,0]],
        [[12,10]], [[38,25]], [[12,40]], [[12,10]],
        [[16,6]], [[10,6]], [[13,3]], [[16, 6]]
      ]
  print("bbox comparison: ", mvbbox_cmp)
  print("rd.bbox2moves(): ", mvbbox)

  print("mvpath comparison: ", mvpath_cmp)
  print("rd.paths2moves():  ", mvpath)

  ###################################################
  print("Test Mark+Cut")
  paths_list_cut=[
        [[0,0], [50,0], [50,50], [0,50], [0,0]]
        ]
  paths_list_mark=[
        [[12,10], [38,25], [12,40], [12,10]],
        [[16,6], [10,6], [13,3], [16, 6]],
        [[60,6], [54,6], [57,3], [60, 6]]
      ]

  rd = Ruida()
  rd.set(nlayers=2)
  rd.set(layer=0, color=[0,255,0], speed=100, power=[10,18], paths=paths_list_mark)
  rd.set(layer=1, color=[255,0,0], speed=30,  power=[40,70], paths=paths_list_cut)

  with open('square_tri_test.rd', 'wb') as fd:
    rd.write(fd)
    print("square_tri_test.rd: odometer: ", rd._odo)

