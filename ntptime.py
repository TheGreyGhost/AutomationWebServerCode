

to do:

upon first call - check against the NTP server
once we have checked the NTP and it matches the actual clock time, don't need to use NTP server again


def gettime_ntp(addr='time.nist.gov'):
    # http://code.activestate.com/recipes/117211-simple-very-sntp-client/
    import socket
    import struct
    import sys
    import time
    TIME1970 = 2208988800L      # Thanks to F.Lundh
    client = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    data = '\x1b' + 47 * '\0'
    client.sendto( data, (addr, 123))
    data, address = client.recvfrom( 1024 )
    if data:
        t = struct.unpack( '!12I', data )[10]
        t -= TIME1970
        return time.ctime(t),t

    # !/usr/bin/env python
    from socket import AF_INET, SOCK_DGRAM
    import sys
    import socket
    import struct, time

    def getNTPTime(host="pool.ntp.org"):
        port = 123
        buf = 1024
        address = (host, port)
        msg = '\x1b' + 47 * '\0'

        # reference time (in seconds since 1900-01-01 00:00:00)
        TIME1970 = 2208988800L  # 1970-01-01 00:00:00

        # connect to server
        client = socket.socket(AF_INET, SOCK_DGRAM)
        client.sendto(msg, address)
        msg, address = client.recvfrom(buf)

        t = struct.unpack("!12I", msg)[10]
        t -= TIME1970
        return time.ctime(t).replace("  ", " ")

    if __name__ == "__main__":
        print
        getNTPTime()