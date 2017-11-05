#! /usr/bin/python3
#
# (c) 2017 Patrick Himmelmann et.al.
# 2017-05-21


end_command(payload):
    data=scramble_bytes(payload)
    checksum=sum(data)
    b1=checksum&0xff
    b0=(checksum>>8)&0xff
    return bytes([b0,b1])+data

def encode_number(n,l=5):
    res=[]
    while n>0:
        res.append(n&0x7f)
        n>>=7
    while len(res)<l:
        res.append(0)
    res.reverse()
    return bytes(res)

def decode_number(x):
    fak=1
    res=0
    for b in reversed(x):
        res+=fak*b
        fak*=0x80
    return res

def format_capture(c):
    for p in c:
        direction=p["_source"]['layers']['udp']['udp.port']=='50200'
        data=unscramble_packet(p,checksum=direction)
        line='-> ' if direction else '<- '
        line+=' '.join([bytes(x).hex() for x in split_messages(data)])
        print(line)

def split_messages(d):
    m=[]
    res=[m]
    for x in d:
        if x&0x80:
            m=[]
            res.append(m)
        m.append(x)
    return res
    


def unscramble_packet(p,checksum=False):
    string=p["_source"]["layers"]["data"]["data.data_raw"]
    if checksum:
        return list(bytes.fromhex(string[:4]))+unscramble_string(string[4:])
    else:
        return unscramble_string(string)

def unscramble_string(s):
    return [unscramble(b) for b in bytes.fromhex(s)]

def unscramble(b):
    res_b=b-1
    if res_b<0: res_b+=0x100
    res_b^=0x88
    fb=res_b&0x80
    lb=res_b&1
    res_b=res_b-fb-lb
    res_b|=lb<<7
    res_b|=fb>>7
    return res_b

def scramble(b):
    fb=b&0x80
    lb=b&1
    res_b=b-fb-lb
    res_b|=lb<<7
    res_b|=fb>>7
    res_b^=0x88
    res_b+=1
    if res_b>0xff:res_b-=0x100
    return res_b

def scramble_bytes(bs):
    return bytes([scramble(b) for b in bs])
def unscramble_bytes(bs):
    return bytes([unscramble(b) for b in bs])

