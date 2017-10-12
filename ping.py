#! /usr/bin/python3
"""
a tiny ping program implement in python
@author: hzd
"""

import socket
import argparse
import struct
import os
import time


class Ping(object):
    ICMP_ECHO_REQUEST = 8
    ICMP_ECHO_REPLY = 0
    ICMP_CODE = 0
    SZ = 60 * 1024

    def __init__(self, addr, time_out=4):
        self.pid = os.getpid()
        self.addr = addr
        self.sock = socket.socket(type=socket.SOCK_RAW, proto=socket.IPPROTO_ICMP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, Ping.SZ)
        self.sock.settimeout(time_out)
        self.sent = 0
        self.recv = 0
        self.init_time = time.time()

    def construct(self):
        hdr_nonck = struct.pack('!BBHHH', Ping.ICMP_ECHO_REQUEST, Ping.ICMP_CODE, 0, self.pid, self.sent)
        sent_time = time.time()
        data = struct.pack('d', sent_time)
        hdr = struct.pack('!BBHHH', Ping.ICMP_ECHO_REQUEST, Ping.ICMP_CODE, self.icmp_cksum(hdr_nonck + data), self.pid, self.sent)
        self.sent += 1
        return hdr + data, sent_time

    def icmp_cksum(self, pkt):
        cksum = 0
        countTo = (len(pkt) / 2) * 2
        count = 0
        while count < countTo:
            thisVal = pkt[count + 1] * 256 + pkt[count]
            cksum = cksum + thisVal
            cksum = cksum & 0xffffffff
            count = count + 2
        if countTo < len(pkt):
            cksum = cksum + ord(pkt[len(pkt) - 1])
            cksum = cksum & 0xffffffff
        cksum = (cksum >> 16) + (cksum & 0xffff)
        cksum = cksum + (cksum >> 16)
        res = ~cksum
        res = res & 0xffff
        res = res >> 8 | (res << 8 & 0xff00)
        return res

    def ping_once(self):
        pkt, sent_time = self.construct()
        self.sock.sendto(pkt, (self.addr, 1))
        while True:
            try:
                data, _ = self.sock.recvfrom(1024)
                proto_type, code, cksum, pk_id, seq = struct.unpack('!bbHHh', data[20:28])
                if proto_type == Ping.ICMP_ECHO_REPLY and pk_id == self.pid and seq == self.sent - 1:
                    time_sent = struct.unpack('d', data[28:])[0]
                    print('{} bytes from {}: seq={} time={:.2f} ms'.
                          format(len(data), self.addr, seq, 1000 * (time.time() - time_sent)))
                    self.recv += 1
                    return
            except socket.timeout:
                print('seq={} packet timeout, lost'.format(self.sent))
                return

    def readloop(self, n=None, delay=1):
        print('PING {} 8(36) data bytes'.format(self.addr))
        try:
            while not n or self.sent < n:
                self.ping_once()
                time.sleep(delay)
        except KeyboardInterrupt:
            self.report_res()
        else:
            self.report_res()

    def report_res(self):
        print()
        print('  {} packs transmitted, {} received, {:.2f}% packet loss, total_time {:.2f}ms'.
              format(self.sent, self.recv, 100*(self.sent-self.recv)/self.sent, int(1000*(time.time()-self.init_time))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='a little ping program in Python')
    parser.add_argument('-v', '--version', metavar='version', type=int,
                        choices=[4, 6], help='specify the ICMP version 4 or 6')
    parser.add_argument('host', type=str, help='specify the destination host')
    parser.add_argument('-n', type=int, metavar='num', help='specify the number of packet to send')
    parser.add_argument('-d', '--delay', type=float, metavar='delay',
                        help='specify the delay time (seconds) to send each packet')
    parser.add_argument('-t', '--timeout', type=float, metavar='timeout',
                        help='specify the timeout time (seconds) to receive packet')
    args = parser.parse_args()
    if args.version == 6:
        print('unsupport now')
    else:
        addr = socket.gethostbyname(args.host)
        n = args.n
        delay = args.delay if args.delay else 1
        timeout = args.timeout if args.timeout else 4
        try:
            Ping(addr, time_out=timeout).readloop(n=n, delay=delay)
        except socket.gaierror:
            print('Unknown host')
