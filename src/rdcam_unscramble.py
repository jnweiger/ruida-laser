#! /usr/bin/python3
#
# (c) 2017 Patrick Himmelmann et.al.
# 2017-05-21
#
# (c) 2017-11-24, juergen@fabmail.org
#

import sys, os

def end_command(payload):
    data=scramble_bytes(payload)
    checksum=sum(data)
    b1=checksum&0xff
    b0=(checksum>>8)&0xff
    return bytes([b0,b1])+data

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

if __name__ == '__main__':
    bstr = open(sys.argv[1], "rb").read()
    data = unscramble_bytes(bstr)
    sys.stdout = os.fdopen(1, "wb")
    sys.stdout.write(data)
