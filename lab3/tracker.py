import random
import socket
import struct
import time

import requests

from helpers import bencode, ExponentialBackoffMixin, log_error, print_lock
from peer import Peer

SOCKET_TIMEOUT = 10  # 10 sec
MAX_MSG_LEN = 1024
PROTO_HEADER = 0x41727101980
MSG_CONNECT = 0
MSG_ANNOUNCE = 1

class TrackerConnector(ExponentialBackoffMixin):
    def __init__(self, client, announce_url):
        super().__init__()
        self.cl = client
        self.announce_url = announce_url
        self.sock = None

        if announce_url.startswith('http'):
            self.announce = self.announce_http
        elif announce_url.startswith('udp'):
            self.announce = self.announce_udp
        else:
            raise ValueError(f'Unsupported tracker protocol for {announce_url}')

    def start(self):
        while True:
            try:
                interval = self.update_peers()
                self.success()
                time.sleep(interval)
            except Exception as e:
                self.fail()
                self.sock = None  # повторим подключение с нуля
                log_error(self, e)
                self.sleep()

    def update_peers(self):
        new_peers, interval = self.announce()

        with print_lock:
            print()
            print(f'Got peers from {self.announce_url}:')
            print(list(new_peers.values()))
            print(f'Next announce after {interval} s')
            print()

        with self.cl.cv_peers:
            # Объединение словарей с пирами. Если пир уже был в словаре,
            # то сохранится старый объект.
            self.cl.peers = new_peers | self.cl.peers
            # Разбудить рабочие потоки, ждущие пира для подключения.
            self.cl.cv_peers.notify_all()
        
        return interval

    def announce_http(self):
        params = {
            'info_hash': self.cl.ti.info_hash,
            'peer_id': self.cl.peer_id,
            'port': 6889,
            'uploaded': self.cl.uploaded,
            'downloaded': self.cl.downloaded,
            'left': self.cl.left,
        }
        if self.cl.downloaded == 0:
            params['event'] = 'started'

        res = requests.get(self.announce_url, params=params)
        if not res.ok:
            raise ConnectionError('Failed to connect to tracker: ' + res.reason)
        
        res = bencode.decode(res.content)
        if 'failure reason' in res:
            raise ConnectionError('Tracker replied with an error: ' + res['failure reason'])
        
        peers = {}
        for p in res['peers']:
            peer = Peer(p['peer id'], p['ip'], p['port'])
            peers[peer.address] = peer

        return peers, res['interval']

    def announce_udp(self):
        if self.sock is None:
            self.connect_udp()

        trans_id = random.randbytes(4)
        connect_msg = struct.pack('>qi4s', PROTO_HEADER, MSG_CONNECT, trans_id)
        self.sock.sendall(connect_msg)
        res_act, res_trid, conn_id = struct.unpack('>i4sq', self.sock.recv(MAX_MSG_LEN))
        if res_act != MSG_CONNECT or res_trid != trans_id:
            raise ConnectionError('Invalid tracker response!')

        trans_id = random.randbytes(4)
        ann_msg = struct.pack('>qi4s20s20sqqqii4siH',
                conn_id,
                MSG_ANNOUNCE,
                trans_id,
                self.cl.ti.info_hash,
                self.cl.peer_id,
                self.cl.downloaded,
                self.cl.left,
                self.cl.uploaded,
                2 if self.cl.downloaded == 0 else 0,
                0,
                random.randbytes(4),
                -1,
                6889,)
        self.sock.sendall(ann_msg)
        resp = self.sock.recv(MAX_MSG_LEN)
        res_act, res_trid, interval = struct.unpack('>i4sI', resp[:12])
        if res_act != MSG_ANNOUNCE or res_trid != trans_id:
            raise ConnectionError('Invalid tracker response!')

        peers = {}
        peers_bytes = resp[20:]
        for i in range(0, len(peers_bytes), 6):
            peer_info = peers_bytes[i:i+6]
            ip = socket.inet_ntoa(peer_info[:4])  # unpack IP to string form
            port = struct.unpack('>H', peer_info[4:])[0]
            peer = Peer('<peer id unknown>', ip, port)
            peers[peer.address] = peer
        
        return peers, interval

    def connect_udp(self):
        host = self.announce_url.removeprefix('udp://')
        host = host.partition('/')[0]  # убрать часть после /
        host, _, port = host.partition(':')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(SOCKET_TIMEOUT)
        self.sock.connect((socket.gethostbyname(host), int(port)))

    def __str__(self):
        return self.announce_url
