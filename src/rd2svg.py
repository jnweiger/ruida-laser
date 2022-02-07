#! /usr/bin/python3
#
# rd2svg.py
#
# Requires:
#  sudo pip3 install svg.py
#  sudo pip3 install typing_extensions
#
# 2022-02-06, v0.1, jw:       initial draught: can tokenize square_tri_test.rd
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
  def __init__(self, buf=None, file=None):
    self._buf  = buf
    self._file  = file


  def skip_bytes(self, n, desc=None):
    r = []
    for i in range(n):
      r.append("%02x" % self._buf[i])
    return n, " ".join(r)


  def laser_offset(self, n, desc=None):
    return n, "laser_offset: " + self.skip_bytes(n, desc)

  def bb_top_left(self, n, desc=None):
    return n, "bb_top_left: " + self.skip_bytes(n, desc)

  def bb_bot_right(self, n, desc=None):
    return n, "bb_bot_right: " + self.skip_bytes(n, desc)

  def feeding(self, n, desc=None):
    return n, "feeding: " + self.skip_bytes(n, desc)

  def layer_speed(self, n, desc=None):
    return n, "layer_speed: " + self.skip_bytes(n, desc)

  def laser_freq(self, n, desc=None):
    return n, "laser_freq: " + self.skip_bytes(n, desc)

  def laser_min_pow(self, n, desc=None):
    return n, "laser_min_pow: " + self.skip_bytes(n, desc)

  def laser_max_pow(self, n, desc=None):
    return n, "laser_max_pow: " + self.skip_bytes(n, desc)

  def laser_min_pow_lay(self, n, desc=None):
    return n, "laser_min_pow_lay: " + self.skip_bytes(n, desc)

  def laser_max_pow_lay(self, n, desc=None):
    return n, "laser_max_pow_lay: " + self.skip_bytes(n, desc)

  def cut_through_pow(self, n, desc=None):
    return n, "cut_through_pow: " + self.skip_bytes(n, desc)

  def move_abs(self, n, desc=None):
    return n, "move_abs: " + self.skip_bytes(n, desc)

  def move_rel(self, n, desc=None):
    return n, "move_rel: " + self.skip_bytes(n, desc)

  def cut_abs(self, n, desc=None):
    return n, "cut_abs: " + self.skip_bytes(n, desc)

  def cut_rel(self, n, desc=None):
    return n, "cut_rel: " + self.skip_bytes(n, desc)

  def cut_horiz(self, n, desc=None):
    return n, "cut_horiz: " + self.skip_bytes(n, desc)

  def cut_vert(self, n, desc=None):
    return n, "cut_vert: " + self.skip_bytes(n, desc)

  def move_horiz(self, n, desc=None):
    return n, "move_horiz: " + self.skip_bytes(n, desc)

  def move_vert(self, n, desc=None):
    return n, "move_vert: " + self.skip_bytes(n, desc)


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
        0x02: ["CA_02", skip_bytes, 1, ":priority"],
        0x03: ["CA_03", skip_bytes, 1],
        0x06: ["Layer_Color", skip_bytes, 1+5, ":layer, :color"],
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
        0x50: ["Bounding_Box_Top_Left", skip_bytes, 5+5, ":abs, :abs"],
        0x51: ["Bounding_Box_Bottom_Right", skip_bytes, 5+5, ":abs, :abs"],
        0x52: ["Layer_Top_Left_E7_52", skip_bytes, 1+5+5, ":layer, :abs, :abs"],
        0x53: ["Layer_Bottom_Right_E7_53", skip_bytes, 1+5+5, ":layer, :abs, :abs"],
        0x54: ["Pen_Draw_Y", skip_bytes, 1+5, ":layer, :abs"],
        0x55: ["Laser_Y_Offset", skip_bytes, 1+5, ":layer, :abs"],
        0x60: ["E7 60", skip_bytes, 1],
        0x61: ["Layer_Top_Left_E7_61", skip_bytes, 1+5+5, ":layer, :abs, :abs"],
        0x62: ["Layer_Bottom_Right_E7_62", skip_bytes, 1+5+5, ":layer, :abs, :abs"]
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
        0x03: ["Laser2_Offset", laser_offset, 5+5, ":abs, :abs" ],
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
        msg += " (" + c[3] + ")"
      else:
        msg = "(" + c[3] + ")"
    return consumed,msg


  def decode(self):
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
            print(out)
            self._buf = self._buf[consumed:]
            pos += consumed

          else:
            print("%5d: %02x %02x second byte not defined in rd_dec" % (pos, b0, self._buf[0]))

        else:
          # single byte command.
          out = "%5d: %02x %s" % (pos, b0, c[0])
          consumed,msg = self.token_method(tok)
          if msg is not None: out += " " + msg;
          print(out)
          self._buf = self._buf[consumed:]
          pos += consumed

      else:
        print("%5d: %02x ERROR: ----------- token not found in rd_dec" % (pos, b0))


p = RuidaParser(buf)
p.decode()

###

paths = [
  svg.Path(
                d=[
                    svg.M(20, 230),
                    svg.L(160, 200),
                    svg.L(50, 360),
                    svg.Z(),
                    svg.M(30, 240),
                    svg.L(140, 210),
                    svg.L(50, 300),
                    svg.Z(),
                ],
                fill="none",
                stroke="blue",
                stroke_width=1,
            ),
]

canvas = svg.SVG(
  width="400mm",
  height="360mm",
  viewBox=svg.ViewBoxSpec(-40, 0, 400, 360),
  xmlns="http://www.w3.org/2000/svg",
  elements=paths,
)

print(canvas)
