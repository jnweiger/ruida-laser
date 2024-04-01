#! /usr/bin/python3
#
# ruidaparser.py
#
# 2022-02-06, v0.1, jw:       Initial draught: can tokenize square_tri_test.rd
# 2022-02-07, v0.2, jw:       Commands added, parameter decoding wip.
# 2022-02-08, v0.3, jw:       Add layer info to paths.
# 2022-02-08, v1.0, jw:       Can convert square_tri_test.rd into a nice svg.
# 2023-01-19, v1.1, jw:       Can pass a stroke_width into to_svg().
# 2024-04-01, v1.2, jw:       Prefixed all token metods with t_
#                             Allow decode params in skip_msg()
#                             Added Direct_Move_Z_rel & friends.
#
import sys

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
    # intializations
    if file and not buf:
      fd = open(file, 'rb')
      self._buf = self.unscramble_bytes(fd.read())
      fd.close()


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
    if res > 0x80000000:      # negative values seen with Z-Move
      res = res - 0x100000000
    return res * 0.001

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

  def decode_percent_float(self, x):
    """
    The magic constant is 1/100 of 14bit all 1s.
    """
    return ( (x[0]<<7) + x[1] ) * 100/0x3fff

  def arg_perc(self, off=0):
    buf = self._buf[off:off+2]
    return off+2, int( self.decode_percent_float(buf) + .5 )

  def arg_perc_f(self, off=0):
    buf = self._buf[off:off+2]
    return off+2, self.decode_percent_float(buf)

  def arg_abs(self, off=0):
    buf = self._buf[off:off+5]
    return off+5, self.decode_number(buf)

  def arg_rel(self, off=0):
    buf = self._buf[off:off+2]
    return off+2, self.decode_relcoord(buf)

  def arg_color(self, off=0):
    buf = self._buf[off:off+5]
    # color, BGR, each value 8 bits, distributed over four 7-bit values
    rgb = list(reversed(list(buf)))
    red   =   rgb[0] +               ((rgb[1] & 0x01) << 7) # red overflows by 1 bit
    green = ((rgb[1] & 0x7e) >> 1) + ((rgb[2] & 0x03) << 6) # green by 2 bits
    blue  = ((rgb[2] & 0x7c) >> 2) + ((rgb[3] & 0x07) << 5) # blue by 3 bits
    return off+5, ((red<<16) + (green<<8) + blue)


  def skip_msg(self, n, desc=None):
    """
        Parameters:
        n: the number of bytes to skip.
        desc: (optional) if it is an array
          - desc[0] is ignored (description string, later printed by token_method() )
          - desc[1:] are either
                - integers, bytes to simply skip before/between decode_*() calls.
                - or one of arg_abs, arg_rel, arg_perc_f
                  to fill an array printed in '[...]' with decoded values.
    """
    buf = self._buf
    r = []
    if len(buf) < n:
      return "ERROR: len(buf)=%d < n=%d" % (len(buf), n)
    for i in range(n):
      r.append("%02x" % buf[i])
    if type(desc) == type([]):
      # r.append('('+desc[0]+')') # already done (later) by our caller token_method
      off = 0
      v = []
      for arg in desc[1:]:
        if type(arg) == type(0):
          off += arg
        else:
          n, val = arg(self, off)
          # v.append(str(buf[off:n])+str(val))
          v.append(val)
          off = n
      r.append("=>"+str(v))
    return " ".join(r)

  def t_skip_bytes(self, n, desc=None):
    """
        parameter: see skip_msg used by skip_msg:
    """
    return n, self.skip_msg(n, desc)


  def t_layer_priority(self, n, desc=None):
    l = self._buf[0]
    self._prio = l
    return 1, "t_layer_priority(%d)" % l

  def t_laser_offset(self, n, desc=None):
    las = self.get_laser(desc[1])
    off, x = self.arg_abs()
    off, y = self.arg_abs(off)
    las['offset'][0] = x
    las['offset'][1] = y
    return off, "t_laser_offset(%d, %.8gmm, %.8gmm)" % (las['n'], x, y)

  def t_bb_top_left(self, n, desc=None):
    off, x = self.arg_abs()
    off, y = self.arg_abs(off)
    if x < self._bbox[0]: self._bbox[0] = x
    if y < self._bbox[1]: self._bbox[1] = y
    return off, "t_bb_top_left(%.8gmm, %.8gmm)" % (x, y)

  def t_lay_top_left(self, n, desc=None):
    l = self.get_layer(self._buf[0])
    off, x = self.arg_abs(1)
    off, y = self.arg_abs(off)
    if x < self._bbox[0]: self._bbox[0] = x
    if y < self._bbox[1]: self._bbox[1] = y
    l['bbox'][0] = x
    l['bbox'][1] = y
    return off, "t_lay_top_left(%d, %.8gmm, %.8gmm)" % (l['n'], x, y)

  def t_bb_bot_right(self, n, desc=None):
    off, x = self.arg_abs()
    off, y = self.arg_abs(off)
    if x > self._bbox[2]: self._bbox[2] = x
    if y > self._bbox[3]: self._bbox[3] = y
    return off, "t_bb_bot_right(%.8gmm, %.8gmm)" % (x, y)

  def t_lay_bot_right(self, n, desc=None):
    l = self.get_layer(self._buf[0])
    off, x = self.arg_abs(1)
    off, y = self.arg_abs(off)
    if x > self._bbox[2]: self._bbox[2] = x
    if y > self._bbox[3]: self._bbox[3] = y
    l['bbox'][2] = x
    l['bbox'][3] = y
    return off, "t_lay_bot_right(%d, %.8gmm, %.8gmm)" % (l['n'], x, y)

  def t_feeding(self, n, desc=None):
    off, x = self.arg_abs()
    off, y = self.arg_abs(off)
    return off, "t_feeding(%.8gmm, %.8gmm)" % (x, y)

  def t_layer_speed(self, n, desc=None):
    l = self.get_layer(self._buf[0])
    off, x = self.arg_abs(1)
    l['speed'] = x
    return off, "t_layer_speed(%d, %.8gmm)" % (l['n'], x)

  def t_layer_color(self, n, desc=None):
    l = self.get_layer(self._buf[0])
    off, rgb = self.arg_color(1)
    l['color'] = "#%06x" % rgb
    return off, "t_layer_color(%d, 0x%06x)" % (l['n'], rgb)

  def t_laser_freq(self, n, desc=None):
    las = self.get_laser(self._buf[0])
    off, x = self.arg_abs(2)
    las['freq'] = x
    return off, "t_laser_freq(%d, %.8g)" % (las['n'], x)

  def t_laser_min_pow(self, n, desc=None):
    las = self.get_laser(desc[1])
    off, x = self.arg_perc()
    las['min_pow'] = x
    return off, "t_laser_min_pow(%d, %d%%)" % (las['n'], x)

  def t_laser_max_pow(self, n, desc=None):
    las = self.get_laser(desc[1])
    off, x = self.arg_perc()
    las['max_pow'] = x
    return off, "t_laser_max_pow(%d, %d%%)" % (las['n'], x)

  def t_laser_min_pow_lay(self, n, desc=None):
    l = self._buf[0]
    las = self.get_laser(desc[1], l)
    off, x = self.arg_perc(1)
    las['min_pow'] = x
    return off, "t_laser_min_pow_lay(%d, %d, %d%%)" % (las['n'], l, x)

  def t_laser_max_pow_lay(self, n, desc=None):
    l = self._buf[0]
    las = self.get_laser(desc[1], l)
    off, x = self.arg_perc(1)
    las['max_pow'] = x
    return off, "t_laser_max_pow_lay(%d, %d, %d%%)" % (las['n'], l, x)

  def t_cut_through_pow(self, n, desc=None):
    return n, "t_cut_through_pow: " + self.skip_msg(n, desc)

  def t_move_abs(self, n, desc=None):
    off, x = self.arg_abs()
    off, y = self.arg_abs(off)
    self.new_path().append([x,y])
    return off, "t_move_abs(%.8gmm, %.8gmm)" % (x, y)

  def t_move_rel(self, n, desc=None):
    off, dx = self.arg_rel()
    off, dy = self.arg_rel(off)
    try:
      xy = self.relative_xy(dx, dy)      # must call relative_xy() before new_path()
      self.new_path().append(xy)
    except:
      # ignore Z moves...
      pass
    return off, "t_move_rel(%.8gmm, %.8gmm)" % (dx, dy)

  def t_cut_abs(self, n, desc=None):
    off, x = self.arg_abs()
    off, y = self.arg_abs(off)
    self.get_path().append([x,y])
    return off, "t_cut_abs(%.8gmm, %.8gmm)" % (x, y)

  def t_cut_rel(self, n, desc=None):
    off, dx = self.arg_rel()
    off, dy = self.arg_rel(off)
    self.get_path().append(self.relative_xy(dx, dy))
    return off, "t_cut_rel(%.8gmm, %.8gmm)" % (dx, dy)

  def t_cut_horiz(self, n, desc=None):
    off, dx = self.arg_rel()
    self.get_path().append(self.relative_xy(dx, 0))
    return n, "t_cut_horiz(%.8gmm)" % dx

  def t_cut_vert(self, n, desc=None):
    off, dy = self.arg_rel()
    self.get_path().append(self.relative_xy(0, dy))
    return n, "t_cut_vert(%.8gmm)" % dy

  def t_move_horiz(self, n, desc=None):
    off, dx = self.arg_rel()
    xy = self.relative_xy(dx, 0)
    self.new_path().append(xy)
    return off, "t_move_horiz(%.8gmm)" % dx

  def t_move_vert(self, n, desc=None):
    off, dy = self.arg_rel()
    xy = self.relative_xy(0, dy)
    self.new_path().append(xy)
    return off, "t_move_vert(%.8gmm)" % dy


  rd_decoder_table = {
    0x88: ["Mov_Abs",   t_move_abs, 5+5, ":abs, :abs" ],
    0x89: ["Mov_Rel",   t_move_rel, 2+2, ":rel, :rel" ],
    0x8a: ["Mov_Horiz", t_move_horiz, 2, ":rel" ],
    0x8b: ["Mov_Vert",  t_move_vert, 2, ":rel" ],
    0xa8: ["Cut_Abs",   t_cut_abs, 5+5, ":abs, :abs" ],
    0xa9: ["Cut_Rel",   t_cut_rel, 2+2, ":rel, :rel" ],
    0xaa: ["Cut_Horiz", t_cut_horiz, 2, ":rel" ],
    0xab: ["Cut_Vert",  t_cut_vert, 2, ":rel" ],
    0xc0: ["C0", t_skip_bytes, 2 ],
    0xc1: ["C1", t_skip_bytes, 2 ],
    0xc2: ["C2", t_skip_bytes, 2 ],
    0xc3: ["C3", t_skip_bytes, 2 ],
    0xc4: ["C4", t_skip_bytes, 2 ],
    0xc5: ["C5", t_skip_bytes, 2 ],
    0xc6:
      {
        0x01: ["Laser_1_Min_Pow_C6_01", t_laser_min_pow, 2, ":power", 1],
        0x02: ["Laser_1_Max_Pow_C6_02", t_laser_max_pow, 2, ":power", 1],
        0x05: ["Laser_3_Min_Pow_C6_05", t_laser_min_pow, 2, ":power", 3],
        0x06: ["Laser_3_Max_Pow_C6_06", t_laser_max_pow, 2, ":power", 3],
        0x07: ["Laser_4_Min_Pow_C6_07", t_laser_min_pow, 2, ":power", 4],
        0x08: ["Laser_4_Max_Pow_C6_08", t_laser_max_pow, 2, ":power", 4],
        0x10: ["Dot time", t_skip_bytes, 5, ":sec"],
        0x12: ["Cut_Open_delay_12",  t_skip_bytes, 5, ":ms"],
        0x13: ["Cut_Close_delay_13", t_skip_bytes, 5, ":ms"],
        0x15: ["Cut_Open_delay_15",  t_skip_bytes, 5, ":ms"],
        0x16: ["Cut_Close_delay_16", t_skip_bytes, 5, ":ms"],
        0x21: ["Laser_2_Min_Pow_C6_21", t_laser_min_pow, 2, ":power", 2],
        0x22: ["Laser_2_Max_Pow_C6_22", t_laser_max_pow, 2, ":power", 2],
        0x31: ["Laser_1_Min_Pow_C6_31", t_laser_min_pow_lay, 1+2, ":layer, :power", 1],
        0x32: ["Laser_1_Max_Pow_C6_32", t_laser_max_pow_lay, 1+2, ":layer, :power", 1],
        0x35: ["Laser_3_Min_Pow_C6_35", t_laser_min_pow_lay, 1+2, ":layer, :power", 3], # 654XG only
        0x36: ["Laser_3_Max_Pow_C6_36", t_laser_max_pow_lay, 1+2, ":layer, :power", 3], # 654XG only
        0x37: ["Laser_4_Min_Pow_C6_37", t_laser_min_pow_lay, 1+2, ":layer, :power", 4], # 654XG only
        0x38: ["Laser_4_Max_Pow_C6_38", t_laser_max_pow_lay, 1+2, ":layer, :power", 4], # 654XG only
        0x41: ["Laser_2_Min_Pow_C6_41", t_laser_min_pow_lay, 1+2, ":layer, :power", 2],
        0x42: ["Laser_2_Max_Pow_C6_42", t_laser_max_pow_lay, 1+2, ":layer, :power", 2],
        0x50: ["Cut_through_power1", t_cut_through_pow, 2, ":power", 1],
        0x51: ["Cut_through_power2", t_cut_through_pow, 2, ":power", 2],
        0x55: ["Cut_through_power3", t_cut_through_pow, 2, ":power", 3],
        0x56: ["Cut_through_power4", t_cut_through_pow, 2, ":power", 4],
        0x60: ["Laser_Freq", t_laser_freq, 1+1+5, ":laser, 0x00, :freq" ]
      },
    0xc7: ["C7", t_skip_bytes, 2 ],
    0xc8: ["C8", t_skip_bytes, 2 ],
    0xc9:
      {
        0x02: ["Speed_C9_02", t_skip_bytes, 5, ":speed", arg_abs ],
        0x04: ["Layer_Speed", t_layer_speed, 1+5, ":layer, :speed" ]
      },
    0xca:
      {
        0x12: ["Blow_off"],
        0x13: ["Blow_on"],
        0x01: ["Flags_CA_01", t_skip_bytes, 1, "flags"],
        0x02: ["Prio", t_layer_priority, 1, ":priority"],         # assign a current layer, for paths to follow
        0x03: ["CA_03", t_skip_bytes, 1],
        0x06: ["Layer_Color", t_layer_color, 1+5, ":layer, :color"],
        0x10: ["CA_10", t_skip_bytes, 1],
        0x22: ["Layer_Count", t_skip_bytes, 1],
        0x41: ["Layer_CA_41", t_skip_bytes, 2, ":layer, -1"]
      },
    0xcc: ["ACK response"],
    0xd7: ["EOF"],
    0xd8:
      {
        0x00: ["Light_RED"],
        0x12: ["UploadFollows"],
      },
    0xd9:
      {
        0x00: ["Direct_Move_X_rel ", t_skip_bytes, 1+5, ":mm", 1, arg_abs],
        0x01: ["Direct_Move_Y_rel ", t_skip_bytes, 1+5, ":mm", 1, arg_abs],
        0x02: ["Direct_Move_Z_rel ", t_skip_bytes, 1+5, ":mm", 1, arg_abs],
      },
    0xda:
      {
        0x00: ["Work_Interval query", t_skip_bytes, 2],
        0x01: ["Work_Interval resp1", t_skip_bytes, 2+5],
        0x02: ["Work_Interval resp2", t_skip_bytes, 2+5+5, ":meter, :meter", 2, arg_abs, arg_abs ],
      },
    0xe6:
      {
        0x01: ["E6_01"]
      },
    0xe7:
      {
        0x00: ["Stop"],
        0x01: ["SetFilename", t_skip_bytes, 0, ":string"],
        0x03: ["Bounding_Box_Top_Left", t_bb_top_left, 5+5, ":abs, :abs"],
        0x04: ["E7 04", t_skip_bytes, 4+5+5, ":abs, :abs"],
        0x05: ["E7_05", t_skip_bytes, 1],
        0x06: ["Feeding", t_feeding, 5+5, ":abs, :abs"], # Feeding1, Distance+Feeding2
        0x07: ["Bounding_Box_Bottom_Right", t_bb_bot_right, 5+5, ":abs, :abs"],
        0x08: ["Bottom_Right_E7_08", t_skip_bytes, 4+5+5, ":abs, :abs"],
        0x13: ["E7 13", t_skip_bytes, 5+5, ":abs, :abs"],
        0x17: ["Bottom_Right_E7_17", t_skip_bytes, 5+5, ":abs, :abs"],
        0x23: ["E7 23", t_skip_bytes, 5+5, ":abs, :abs"],
        0x24: ["E7 24", t_skip_bytes, 1],
        0x50: ["Bounding_Box_Top_Left", t_bb_top_left, 5+5, ":abs, :abs"],
        0x51: ["Bounding_Box_Bottom_Right", t_bb_bot_right, 5+5, ":abs, :abs"],
        0x52: ["Layer_Top_Left_E7_52", t_lay_top_left, 1+5+5, ":layer, :abs, :abs"],
        0x53: ["Layer_Bottom_Right_E7_53", t_lay_bot_right, 1+5+5, ":layer, :abs, :abs"],
        0x54: ["Pen_Draw_Y", t_skip_bytes, 1+5, ":layer, :abs"],
        0x55: ["Laser_Y_Offset", t_skip_bytes, 1+5, ":layer, :abs"],
        0x60: ["E7 60", t_skip_bytes, 1],
        0x61: ["Layer_Top_Left_E7_61", t_lay_top_left, 1+5+5, ":layer, :abs, :abs"],
        0x62: ["Layer_Bottom_Right_E7_62", t_lay_bot_right, 1+5+5, ":layer, :abs, :abs"]
      },
    0xe8:
      {
        0x01: ["FileStore", t_skip_bytes, 1+1, "0x00, :number, :string" ],
        0x02: ["PrepFilename"],
      },
    0xea: ["EA", t_skip_bytes, 1],
    0xeb: ["Finish"],
    0xf0: ["Magic88"],
    0xf1:
      {
        0x00: ["Start0", t_skip_bytes, 1 ],
        0x01: ["Start1", t_skip_bytes, 1 ],
        0x02: ["Start2", t_skip_bytes, 1 ],
        0x03: ["Laser2_Offset", t_laser_offset, 5+5, ":abs, :abs", 2 ],
        0x04: ["Enable_Feeding(auto?)", t_skip_bytes, 1, ":bool" ]
      },
    0xf2:
      {
        0x00: ["F2 00", t_skip_bytes, 1 ],
        0x01: ["F2 01", t_skip_bytes, 1 ],
        0x02: ["F2 02", t_skip_bytes, 10 ],
        0x03: ["F2 03", t_skip_bytes, 5+5, ":abs, :abs" ],
        0x04: ["Bottom_Right_F2_04", t_skip_bytes, 5+5, ":abs, :abs" ],
        0x05: ["Bottom_Right_F2_05", t_skip_bytes, 4+5+5, "-4, :abs, :abs" ],
        0x06: ["F2 06", t_skip_bytes, 5+5, ":abs, :abs" ],
        0x07: ["F2 07", t_skip_bytes, 1 ]
      }
  }

  def token_method(self, c):
    """
      disentangle a description list from the rd_decoder_table into a proper method call
      c[0] is the name of the decoder table entry
      c[1] is the t_... method to call
      c[2] (optional first paramter to the method)
           number of bytes to consume (the method can decide differenly)
      c[3] (optional second parameter to the method)
            description string
      more arguments are optional,  they are passed as an array into the second parameter.

      token methods are expected to return two values:
        n, the number of bytes actually consumed.
        msg, an infomational message to print.
      token methods may also look into self.buf to actually examine the buffer contents.
      (the buffer position is automatically advanced by n by the caller.)
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


  def decode(self, buf=None, debug=False):
    """
      Go through the buffer, byte by byte, and call token methods from the
      rd_decoder_table identified by either a one byte or a two byte token.
      For signature of the method calls see token_method()
      The contents of the buffer must already be unscambled.
    """
    debugfile = sys.stderr
    if debug not in (True, False):
        debug = True
        debugfile = sys.stdout
    if buf is not None:
        self._buf = buf
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
            if debug: print(out, file=debugfile)
            self._buf = self._buf[consumed:]
            pos += consumed

          else:
            if debug: print("%5d: %02x %02x second byte not defined in rd_dec" % (pos, b0, self._buf[0]), file=debugfile)

        else:
          # single byte command.
          out = "%5d: %02x %s" % (pos, b0, tok[0])
          try:
            consumed,msg = self.token_method(tok)
          except:
            print(out + "token_method failed", tok, file=debugfile)
            consumed,msg = self.token_method(tok)
            
          if msg is not None: out += " " + msg;
          if debug: print(out, file=debugfile)
          self._buf = self._buf[consumed:]
          pos += consumed

      else:
        if debug: print("%5d: %02x ERROR: ----------- token not found in rd_dec" % (pos, b0), file=debugfile)

  def svg_number(self, x):
    ## must not be scientific format.
    ## must not have thousands comma, or dot.
    ## must always use decimal dot, not comma
    ## should not have trailing decimal zeros or trailing dot.
    # locale.setlocale(locale.LC_ALL, 'C')      # not neeed. "%f" seems to be locale agnostic. That is a good thing!
    n = "%.10f" % x
    if '.' in n:
      while n[-1] == '0': n = n[:-1]
    if n[-1] == '.': n = n[:-1]
    return n

  def to_svg(self, stroke_width=1):
    w = self.svg_number(self._bbox[2]-self._bbox[0])
    h = self.svg_number(self._bbox[3]-self._bbox[1])
    x = self.svg_number(self._bbox[0])
    y = self.svg_number(self._bbox[1])

    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s %s %s %s" width="%smm" height="%smm">' % (x,y,w,h,w,h)

    elems = [svg]

    for path in self._paths:
      n = len(path['data'])
      d = []
      for i in range(n):
        v = path['data'][i]
        if i == 0:
          d.append("M %s %s" % (self.svg_number(v[0]), self.svg_number(v[1])))
        elif i > 0 and i == n-1 and v == path['data'][0]:
          d.append("Z")
        else:
          d.append("L %s %s" % (self.svg_number(v[0]), self.svg_number(v[1])))
      color="blue"
      if path.get('layer') and path['layer'].get('color'):
        color = path['layer']['color']
      elems.append('<path stroke="%s" stroke-width="%s" fill="none" d="%s"/>' % (color, stroke_width, ' '.join(d)))
    elems.append("</svg>")
    return "\n".join(elems)

