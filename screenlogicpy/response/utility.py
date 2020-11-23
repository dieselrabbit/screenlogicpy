import struct

def getSome(want, buff, offset):
    fmt = "<" + want
    newoffset = offset + struct.calcsize(fmt)
    return struct.unpack_from(fmt, buff, offset)[0], newoffset

def getString(buff, offset):
    fmtLen = "<I"
    offsetLen = offset + struct.calcsize(fmtLen)
    sLen = struct.unpack_from(fmtLen, buff, offset)[0]
    if sLen % 4 != 0:
        sLen += 4 - sLen % 4
  
    fmt = "<{}{}".format(sLen, "s")
    newoffset = offsetLen + struct.calcsize(fmt)
    return struct.unpack_from(fmt, buff, offsetLen)[0], newoffset

def getArray(buff, offset):
    itemCount, offset = getSome("I", buff, offset)
    items = [0 for x in range(itemCount)]
    for i in range(itemCount):
        items[i] , offset = getSome("B", buff, offset)
    offsetPad = 0
    if itemCount % 4 != 0:
        offsetPad = (4 - itemCount % 4) % 4
        offset += offsetPad
    return items, offset
