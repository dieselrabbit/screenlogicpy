import struct
from slgateway.const import header, code


def makeMessageString(string):
    data = string.encode()
    length = len(data)
    pad = 4 - (length % 4)  # pad 'x' to multiple of 4
    fmt = "<I" + str(length) + "s" + str(pad) + "x"
    return struct.pack(fmt, length, data)

def getMessageString(data):
    length = len(data)
    size = struct.unpack_from("<I", data, 0)[0]
    return struct.unpack_from("<" + str(size) + "s", 
                              data, 
                              struct.calcsize("<I"))[0].decode("utf-8")

# Protocol header for every (non-datagram) message sent to/from
# the gateway. 
# This header describes the first 8 bytes:
# 0          2          4           8                              N
# | MSG CD 1 | MSG CD 2 | Data Size | Message Data (parameters) -> |
 
# appends a header to an optional already formatted message.
def makeMessage(msgCode2, messageData=b''):
    return struct.pack(header.fmt + str(len(messageData)) + "s", 
                       code.MSG_CODE_1, 
                       msgCode2, 
                       len(messageData), 
                       messageData)

# takes the header off of the pool message and returns just the message part
def takeMessage(message):
    if not message:
        sys.stderr.write(
            "WARNING: {}: no data to decodeMessage()\n".format(
                me
                )
            )
        return
    messageBytes = len(message) - header.length
    rcvCode1, rcvCode2,\
        rcvLen, data = struct.unpack(header.fmt + str(messageBytes) + "s",
                                     message)
    if(rcvLen != messageBytes):
        sys.stderr.write(
            "WARNING: {}: rcvLen({}) != messageBytes({}).\n".format(
                me, rcvLen, messageBytes
                )
            )
    if(rcvCode2 == code.UNKNOWN_ANSWER):
        sys.stderr.write(
            "WARNING: {}: rcvCode2({}) != expectCode2.\n".format(
                me, rcvCode2
                )
            )
    return rcvCode2, data # return raw data
