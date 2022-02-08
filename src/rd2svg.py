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
import svg
import ruida

rd = ruida.Ruida()

fd = open(sys.argv[1], 'rb')
buf = rd.unscramble_bytes(fd.read())

class RuidaParser():
  """
  """
  def __init__(self, buf=None, file=None, debug=False):
    # input
    self._buf  = buf
    self._file  = file
    # output
    self._bbox = [ 10e9, 10e9, -10e9, -10e9 ]
    self._paths = []
    self._layer = {}
    self._laser = {}

  def get_layer(self, n):
    if n not in self._layer:
      self._layer[n] =  { 'n': n, 'bbox':[0,0,0,0], 'laser': {} }
    return self._layer[n]

  def get_laser(self, n, lay=None):
    if lay is not None:
      l = self.get_layer(lay)
      if n not in l['laser']:
        l['laser'][n] =  { 'n': n, 'offset':[0,0], 'layer':lay }
      return l['laser'][n]
    if n not in self._laser:
      self._laser[n] =  { 'n': n, 'offset':[0,0] }
    return self._laser[n]

  def new_path(self):
    p = { 'data':[], 'n':len(self._paths), 'layer':self._layer.get(self._prio, self._prio) }
    self._paths.append(p)
    return p['data']

  def get_path(self):
    if not self._paths:
      self.new_path().append([0,0])   # Moveto missing? Assume we start at origin.
    return self._paths[-1]['data']

  def relative_xy(self, x=0, y=0):
    if not self._paths:
      self.new_path().append([0,0])   # Need current position, before anythingy? Assume we start at origin.
    current = self._paths[-1]['data'][-1]
    return [ current[0]+x, current[1]+y ]

  def decode_number(self, x):
    "used with a bytes() array of length 5"
    fak=1
    res=0
    for b in reversed(x):
      res+=fak*b
      fak*=0x80
    return 0.001 * res

  def decode_relcoord(self, x):
    """
    using the first two elements of array x
    relative position in micrometer; signed (2s complement)
    """
    r = (x[0] << 7) + x[1]
    if r > 16383 or r < 0:
      raise ValueError("Not a rel coord: " + repr(x[0:2]))
    if r > 8191: return 0.001 * (r-16384)
    else:        return 0.001 * r

  def decode_percent(self, x):
    """
    The magic constant is 1/100 of 14bit all 1s.
    """
    return int( ( (x[0]<<7) + x[1] ) * 100/0x3fff + .5)

  def arg_perc(self, off=0):
    buf = self._buf[off:off+2]
    return off+2, self.decode_percent(buf)

  def arg_abs(self, off=0):
    buf = self._buf[off:off+5]
    return off+5, self.decode_number(buf)

  def arg_rel(self, off=0):
    buf = self._buf[off:off+2]
    return off+2, self.decode_relcoord(buf)


  def skip_msg(self, n, buf=None):
    if buf is None: buf = self._buf
    r = []
    for i in range(n):
      r.append("%02x" % buf[i])
    return " ".join(r)

  def skip_bytes(self, n, desc=None):
    return n, self.skip_msg(n)


  def layer_priority(self, n, desc=None):
    l = self._buf[0]
    self._prio = l
    return 1, "layer_priority(%d)" % l

  def laser_offset(self, n, desc=None):
    las = self.get_laser(desc[1])
    off, x = self.arg_abs()
    off, y = self.arg_abs(off)
    las['offset'][0] = x
    las['offset'][1] = y
    return off, "laser_offset(%d, %.8gmm, %.8gmm)" % (las['n'], x, y)

  def bb_top_left(self, n, desc=None):
    off, x = self.arg_abs()
    off, y = self.arg_abs(off)
    if x < self._bbox[0]: self._bbox[0] = x
    if y < self._bbox[1]: self._bbox[1] = y
    return off, "bb_top_left(%.8gmm, %.8gmm)" % (x, y)

  def lay_top_left(self, n, desc=None):
    l = self.get_layer(self._buf[0])
    off, x = self.arg_abs(1)
    off, y = self.arg_abs(off)
    if x < self._bbox[0]: self._bbox[0] = x
    if y < self._bbox[1]: self._bbox[1] = y
    l['bbox'][0] = x
    l['bbox'][1] = y
    return off, "lay_top_left(%d, %.8gmm, %.8gmm)" % (l['n'], x, y)

  def bb_bot_right(self, n, desc=None):
    off, x = self.arg_abs()
    off, y = self.arg_abs(off)
    if x > self._bbox[2]: self._bbox[2] = x
    if y > self._bbox[3]: self._bbox[3] = y
    return off, "bb_bot_right(%.8gmm, %.8gmm)" % (x, y)

  def lay_bot_right(self, n, desc=None):
    l = self.get_layer(self._buf[0])
    off, x = self.arg_abs(1)
    off, y = self.arg_abs(off)
    if x > self._bbox[2]: self._bbox[2] = x
    if y > self._bbox[3]: self._bbox[3] = y
    l['bbox'][2] = x
    l['bbox'][3] = y
    return off, "lay_bot_right(%d, %.8gmm, %.8gmm)" % (l['n'], x, y)

  def feeding(self, n, desc=None):
    off, x = self.arg_abs()
    off, y = self.arg_abs(off)
    return off, "feeding(%.8gmm, %.8gmm)" % (x, y)

  def layer_speed(self, n, desc=None):
    l = self.get_layer(self._buf[0])
    off, x = self.arg_abs(1)
    l['speed'] = x
    return off, "layer_speed(%d, %.8gmm)" % (l['n'], x)

  def layer_color(self, n, desc=None):
    l = self.get_layer(self._buf[0])
    off, col = self.arg_abs(1)
    l['color'] = col
    return off, "layer_color(%d, %d)" % (l['n'], col)

  def laser_freq(self, n, desc=None):
    las = self.get_laser(self._buf[0])
    off, x = self.arg_abs(2)
    las['freq'] = x
    return off, "laser_freq(%d, %.8g)" % (las['n'], x)

  def laser_min_pow(self, n, desc=None):
    las = self.get_laser(desc[1])
    off, x = self.arg_perc()
    las['min_pow'] = x
    return off, "laser_min_pow(%d, %d%%)" % (las['n'], x)

  def laser_max_pow(self, n, desc=None):
    las = self.get_laser(desc[1])
    off, x = self.arg_perc()
    las['max_pow'] = x
    return off, "laser_max_pow(%d, %d%%)" % (las['n'], x)

  def laser_min_pow_lay(self, n, desc=None):
    l = self._buf[0]
    las = self.get_laser(desc[1], l)
    off, x = self.arg_perc(1)
    las['min_pow'] = x
    return off, "laser_min_pow_lay(%d, %d, %d%%)" % (las['n'], l, x)

  def laser_max_pow_lay(self, n, desc=None):
    l = self._buf[0]
    las = self.get_laser(desc[1], l)
    off, x = self.arg_perc(1)
    las['max_pow'] = x
    return off, "laser_max_pow_lay(%d, %d, %d%%)" % (las['n'], l, x)

  def cut_through_pow(self, n, desc=None):
    return n, "cut_through_pow: " + self.skip_msg(n)

  def move_abs(self, n, desc=None):
    off, x = self.arg_abs()
    off, y = self.arg_abs(off)
    self.new_path().append([x,y])
    return off, "move_abs(%.8gmm, %.8gmm)" % (x, y)

  def move_rel(self, n, desc=None):
    off, dx = self.arg_rel()
    off, dy = self.arg_rel(off)
    xy = self.relative_xy(dx, dy)      # must call relative_xy() before new_path()
    self.new_path().append(xy)
    return off, "move_rel(%.8gmm, %.8gmm)" % (dx, dy)

  def cut_abs(self, n, desc=None):
    off, x = self.arg_abs()
    off, y = self.arg_abs(off)
    self.get_path().append([x,y])
    return off, "cut_abs(%.8gmm, %.8gmm)" % (x, y)

  def cut_rel(self, n, desc=None):
    off, dx = self.arg_rel()
    off, dy = self.arg_rel(off)
    self.get_path().append(self.relative_xy(dx, dy))
    return off, "cut_rel(%.8gmm, %.8gmm)" % (dx, dy)

  def cut_horiz(self, n, desc=None):
    off, dx = self.arg_rel()
    self.get_path().append(self.relative_xy(dx, 0))
    return n, "cut_horiz(%.8gmm)" % dx

  def cut_vert(self, n, desc=None):
    off, dy = self.arg_rel()
    self.get_path().append(self.relative_xy(0, dy))
    return n, "cut_vert(%.8gmm)" % dy

  def move_horiz(self, n, desc=None):
    off, dx = self.arg_rel()
    xy = self.relative_xy(dx, 0)
    self.new_path().append(xy)
    return off, "move_horiz(%.8gmm)" % dx

  def move_vert(self, n, desc=None):
    off, dy = self.arg_rel()
    xy = self.relative_xy(0, dy)
    self.new_path().append(xy)
    return off, "move_vert(%.8gmm)" % dy


  rd_decoder_table = {
    0x88: ["Mov_Abs", move_abs, 5+5, ":abs, :abs" ],
    0x89: ["Mov_Rel", move_rel, 2+2, ":rel, :rel" ],
    0x8a: ["Mov_Horiz", move_horiz, 2, ":rel" ],
    0x8b: ["Mov_Vert", move_vert, 2, ":rel" ],
    0xa8: ["Cut_Abs", cut_abs, 5+5, ":abs, :abs" ],
    0xa9: ["Cut_Rel", cut_rel, 2+2, ":rel, :rel" ],
    0xaa: ["Cut_Horiz", cut_horiz, 2, ":rel" ],
    0xab: ["Cut_Vert", cut_vert, 2, ":rel" ],
    0xc0: ["C0", skip_bytes, 2 ],
    0xc1: ["C1", skip_bytes, 2 ],
    0xc2: ["C2", skip_bytes, 2 ],
    0xc3: ["C3", skip_bytes, 2 ],
    0xc4: ["C4", skip_bytes, 2 ],
    0xc5: ["C5", skip_bytes, 2 ],
    0xc6:
      {
        0x01: ["Laser_1_Min_Pow_C6_01", laser_min_pow, 2, ":power", 1],
        0x02: ["Laser_1_Max_Pow_C6_02", laser_max_pow, 2, ":power", 1],
        0x05: ["Laser_3_Min_Pow_C6_05", laser_min_pow, 2, ":power", 3],
        0x06: ["Laser_3_Max_Pow_C6_06", laser_max_pow, 2, ":power", 3],
        0x07: ["Laser_4_Min_Pow_C6_07", laser_min_pow, 2, ":power", 4],
        0x08: ["Laser_4_Max_Pow_C6_08", laser_max_pow, 2, ":power", 4],
        0x10: ["Dot time", skip_bytes, 5, ":sec"],
        0x12: ["Cut_Open_delay_12",  skip_bytes, 5, ":ms"],
        0x13: ["Cut_Close_delay_13", skip_bytes, 5, ":ms"],
        0x15: ["Cut_Open_delay_15",  skip_bytes, 5, ":ms"],
        0x16: ["Cut_Close_delay_16", skip_bytes, 5, ":ms"],
        0x21: ["Laser_2_Min_Pow_C6_21", laser_min_pow, 2, ":power", 2],
        0x22: ["Laser_2_Max_Pow_C6_22", laser_max_pow, 2, ":power", 2],
        0x31: ["Laser_1_Min_Pow_C6_31", laser_min_pow_lay, 1+2, ":layer, :power", 1],
        0x32: ["Laser_1_Max_Pow_C6_32", laser_max_pow_lay, 1+2, ":layer, :power", 1],
        0x35: ["Laser_3_Min_Pow_C6_35", laser_min_pow_lay, 1+2, ":layer, :power", 3], # 654XG only
        0x36: ["Laser_3_Max_Pow_C6_36", laser_max_pow_lay, 1+2, ":layer, :power", 3], # 654XG only
        0x37: ["Laser_4_Min_Pow_C6_37", laser_min_pow_lay, 1+2, ":layer, :power", 4], # 654XG only
        0x38: ["Laser_4_Max_Pow_C6_38", laser_max_pow_lay, 1+2, ":layer, :power", 4], # 654XG only
        0x41: ["Laser_2_Min_Pow_C6_41", laser_min_pow_lay, 1+2, ":layer, :power", 2],
        0x42: ["Laser_2_Max_Pow_C6_42", laser_max_pow_lay, 1+2, ":layer, :power", 2],
        0x50: ["Cut_through_power1", cut_through_pow, 2, ":power", 1],
        0x51: ["Cut_through_power2", cut_through_pow, 2, ":power", 2],
        0x55: ["Cut_through_power3", cut_through_pow, 2, ":power", 3],
        0x56: ["Cut_through_power4", cut_through_pow, 2, ":power", 4],
        0x60: ["Laser_Freq", laser_freq, 1+1+5, ":laser, 0x00, :freq" ]
      },
    0xc7: ["C7", skip_bytes, 2 ],
    0xc8: ["C8", skip_bytes, 2 ],
    0xc9:
      {
        0x02: ["Speed_C9", skip_bytes, 5, ":speed" ],
        0x04: ["Layer_Speed", layer_speed, 1+5, ":layer, :speed" ]
      },
    0xca:
      {
        0x12: ["Blow_off"],
        0x13: ["Blow_on"],
        0x01: ["Flags_CA_01", skip_bytes, 1, "flags"],
        0x02: ["Prio", layer_priority, 1, ":priority"],         # assign a current layer, for paths to follow
        0x03: ["CA_03", skip_bytes, 1],
        0x06: ["Layer_Color", layer_color, 1+5, ":layer, :color"],
        0x10: ["CA_10", skip_bytes, 1],
        0x22: ["Layer_Count", skip_bytes, 1],
        0x41: ["Layer_CA_41", skip_bytes, 2, ":layer, -1"]
      },
    0xd7: ["EOF"],
    0xd8:
      {
        0x00: ["Light_RED"],
        0x12: ["UploadFollows"],
      },
    0xda: [ "Work_Interval", skip_bytes, 3+5+5, "-3, :meter, :meter" ],
    0xe6:
      {
        0x01: ["E6_01"]
      },
    0xe7:
      {
        0x00: ["Stop"],
        0x01: ["SetFilename", skip_bytes, 0, ":string"],
        0x03: ["Bounding_Box_Top_Left", bb_top_left, 5+5, ":abs, :abs"],
        0x04: ["E7 04", skip_bytes, 4+5+5, ":abs, :abs"],
        0x05: ["E7_05", skip_bytes, 1],
        0x06: ["Feeding", feeding, 5+5, ":abs, :abs"], # Feeding1, Distance+Feeding2
        0x07: ["Bounding_Box_Bottom_Right", bb_bot_right, 5+5, ":abs, :abs"],
        0x08: ["Bottom_Right_E7_08", skip_bytes, 4+5+5, ":abs, :abs"],
        0x13: ["E7 13", skip_bytes, 5+5, ":abs, :abs"],
        0x17: ["Bottom_Right_E7_17", skip_bytes, 5+5, ":abs, :abs"],
        0x23: ["E7 23", skip_bytes, 5+5, ":abs, :abs"],
        0x24: ["E7 24", skip_bytes, 1],
        0x50: ["Bounding_Box_Top_Left", bb_top_left, 5+5, ":abs, :abs"],
        0x51: ["Bounding_Box_Bottom_Right", bb_bot_right, 5+5, ":abs, :abs"],
        0x52: ["Layer_Top_Left_E7_52", lay_top_left, 1+5+5, ":layer, :abs, :abs"],
        0x53: ["Layer_Bottom_Right_E7_53", lay_bot_right, 1+5+5, ":layer, :abs, :abs"],
        0x54: ["Pen_Draw_Y", skip_bytes, 1+5, ":layer, :abs"],
        0x55: ["Laser_Y_Offset", skip_bytes, 1+5, ":layer, :abs"],
        0x60: ["E7 60", skip_bytes, 1],
        0x61: ["Layer_Top_Left_E7_61", lay_top_left, 1+5+5, ":layer, :abs, :abs"],
        0x62: ["Layer_Bottom_Right_E7_62", lay_bot_right, 1+5+5, ":layer, :abs, :abs"]
      },
    0xe8:
      {
        0x01: ["FileStore", skip_bytes, 1+1, "0x00, :number, :string" ],
        0x02: ["PrepFilename"],
      },
    0xea: ["EA", skip_bytes, 1],
    0xeb: ["Finish"],
    0xf0: ["Magic88"],
    0xf1:
      {
        0x00: ["Start0", skip_bytes, 1 ],
        0x01: ["Start1", skip_bytes, 1 ],
        0x02: ["Start2", skip_bytes, 1 ],
        0x03: ["Laser2_Offset", laser_offset, 5+5, ":abs, :abs", 2 ],
        0x04: ["Enable_Feeding(auto?)", skip_bytes, 1, ":bool" ]
      },
    0xf2:
      {
        0x00: ["F2 00", skip_bytes, 1 ],
        0x01: ["F2 01", skip_bytes, 1 ],
        0x02: ["F2 02", skip_bytes, 10 ],
        0x03: ["F2 03", skip_bytes, 5+5, ":abs, :abs" ],
        0x04: ["Bottom_Right_F2_04", skip_bytes, 5+5, ":abs, :abs" ],
        0x05: ["Bottom_Right_F2_05", skip_bytes, 4+5+5, "-4, :abs, :abs" ],
        0x06: ["F2 06", skip_bytes, 5+5, ":abs, :abs" ],
        0x07: ["F2 07", skip_bytes, 1 ]
      }
  }

  def token_method(self, c):
    """
      diesentangle a description list from the rd_decoder_table into a proper method call
    """
    consumed,msg = 0,None
    if len(c) == 2:
      return c[1](self)
    elif len(c) == 3:
      return c[1](self, c[2])
    elif len(c) >= 4:
      consumed,msg = c[1](self, c[2], c[3:])
      if msg is None:
        msg = "(" + c[3] + ")"
      else:
        msg += " (" + c[3] + ")"
    return consumed,msg


  def decode(self, debug=False):
    """
      go through the buffer, byte by byte, and call token methods from the rd_decoder_table identified by
      either a one byte or a two byte token.
    """
    pos = -1
    while len(self._buf):
      b0 = self._buf[0]
      self._buf = self._buf[1:]
      pos +=1
      tok = self.rd_decoder_table.get(b0)

      if tok:
        if type(tok) == type({}):
          # multi byte command
          b1 = self._buf[0]
          c = tok.get(b1)
          if c:
            self._buf = self._buf[1:]
            pos +=1
            out = "%5d: %02x %02x %s" % (pos, b0, b1, c[0])
            consumed,msg = self.token_method(c)
            if msg is not None: out += " " + msg;
            if debug: print(out, file=sys.stderr)
            self._buf = self._buf[consumed:]
            pos += consumed

          else:
            if debug: print("%5d: %02x %02x second byte not defined in rd_dec" % (pos, b0, self._buf[0]), file=sys.stderr)

        else:
          # single byte command.
          out = "%5d: %02x %s" % (pos, b0, tok[0])
          consumed,msg = self.token_method(tok)
          if msg is not None: out += " " + msg;
          if debug: print(out, file=sys.stderr)
          self._buf = self._buf[consumed:]
          pos += consumed

      else:
        if debug: print("%5d: %02x ERROR: ----------- token not found in rd_dec" % (pos, b0), file=sys.stderr)


p = RuidaParser(buf)
p.decode(debug=False)
from pprint import pprint
if True: pprint({ 'p':p._paths, 'bbox':p._bbox, 'las':p._laser}, depth=5, stream=sys.stderr)

###

d = []
for path in p._paths:
  n = len(path['data'])
  for i in range(n):
    v = path['data'][i]
    if i == 0:
      d.append(svg.M(v[0], v[1]))
    elif i > 0 and i == n-1 and v == path['data'][0]:
      d.append(svg.Z())
    else:
      d.append(svg.L(v[0], v[1]))

paths = [
  svg.Path(
                d=d,
                fill="none",
                stroke="blue",
                stroke_width=1,
            ),
]

width=p._bbox[2]-p._bbox[0]
height=p._bbox[3]-p._bbox[1]

canvas = svg.SVG(
  width="%.8gmm" % width,
  height="%.8gmm" % height,
  viewBox=svg.ViewBoxSpec(p._bbox[0], p._bbox[1], width, height),
  xmlns="http://www.w3.org/2000/svg",
  elements=paths,
)

print(canvas)
