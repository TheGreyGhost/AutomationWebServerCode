import socket
import struct
import time
import errorhandler
import select
import subprocess

class TimeServerError(OSError):
    pass


class TrueTime:
    m_ntp_server_hostname = None
    m_rpi_has_synced = False
    m_max_timeout = 0
    m_time_tolerance = 0

    # def __init__(self, hostname, max_timeout, time_tolerance):
    #     """
    #     set up the class
    #     :param hostname: the host name of the ntp server eg time.nist.gov
    #     :param max_timeout: the maximum time in seconds to wait for a reply
    #     :param time_tolerance: the amount of error tolerated in the time value to consider the rpi synchronised
    #     """
    #
    #     if max_timeout < 0 or max_timeout > 60:
    #         errorhandler.logwarn("Unreasonable max_timeout {}, set to 10 seconds".format(max_timeout))
    #         max_timeout = 10
    #     if time_tolerance < 0 or time_tolerance > 60:
    #         errorhandler.logwarn("Unreasonable time_tolerance {}, set to 10 seconds".format(time_tolerance))
    #         time_tolerance = 10
    #
    #     self.m_ntp_server_hostname = hostname
    #     self.m_max_timeout = max_timeout
    #     self.m_time_tolerance = time_tolerance

    def __init__(self, max_timeout):
        """
        set up the class
        :param max_timeout: the maximum time in seconds to wait for a reply
        """

        if max_timeout < 0 or max_timeout > 60:
            errorhandler.logwarn("Unreasonable max_timeout {}, set to 10 seconds".format(max_timeout))
            max_timeout = 10
        # if time_tolerance < 0 or time_tolerance > 60:
        #     errorhandler.logwarn("Unreasonable time_tolerance {}, set to 10 seconds".format(time_tolerance))
        #     time_tolerance = 10
        #
        # self.m_ntp_server_hostname = hostname
        self.m_max_timeout = max_timeout
        # self.m_time_tolerance = time_tolerance

    def get_true_time(self):
        """
        gets the true time
        may take some time to return (user defined timeout, up to 60 seconds)
        :return: number of seconds since 1970 1st jan 0:00:00 ("unixtime")
        throws a TimeServerError if the true time couldn't be obtained
        """

        # algorithm is:
        # if the rpi clock has previously been synchronised, just return the rpi time
        # otherwise, check whether the clock is synchronised by comparing with the time from an NTP server
        #once we have checked the NTP and it matches the actual clock time, don't need to use NTP server again

        if self.m_rpi_has_synced or self.check_if_rpi_time_has_synchronised():
            self.m_rpi_has_synced = True
            return time.time()
        raise TimeServerError("Raspberry Pi time is not synchronised yet")

    def check_if_rpi_time_has_synchronised(self):
        """
        checks if the rpi has synchronised itself with an ntp server
        :return: true if synchronised, false if not
        """
        try:
            result = subprocess.run("timedatectl", stdout=subprocess.PIPE, check=True,
                                    text=True, timeout=self.m_max_timeout)

      Local time: Fri 2019-03-01 19:30:31 ACDT
  Universal time: Fri 2019-03-01 09:00:31 UTC
        RTC time: n/a
       Time zone: Australia/Adelaide (ACDT, +1030)
 Network time on: yes
NTP synchronized: yes
 RTC in local TZ: no


        except Exception as e:
            errorhandler.exception(e)
            return False

    # doesn't work for some reason
    def get_ntp_time(self):
        """
        gets the current time from an NTP server
        :return: number of seconds since 1970 1st jan 0:00:00 ("unixtime")
        raise exception if couldn't be obtained
        """
        # http://code.activestate.com/recipes/117211-simple-very-sntp-client/
        TIME1970 = 2208988800      # Thanks to F.Lundh

        port = 123
        buffer_size = 1024
        hostname_and_port = (self.m_ntp_server_hostname, port)
        client = None
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            request_msg = b'\x1b' + 47 * b'\0'
            client.sendto(request_msg, hostname_and_port)

            readables, writables, errors = select.select([client], [], [], self.m_max_timeout)
            if not client in readables:
                raise TimeServerError("No reply from {} within {} seconds".format(self.m_ntp_server_hostname, self.m_max_timeout))

            data, remote_ip_port = client.recvfrom(buffer_size)

        finally:
            if client:
                client.close()

        if not data:
            raise TimeServerError(
                "No reply from {} within {} seconds".format(self.m_ntp_server_hostname, self.m_max_timeout))
        t = struct.unpack('!12I', data)[10]
        t -= TIME1970
        return t

