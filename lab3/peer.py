import socket
import struct

from helpers import ExponentialBackoffMixin, COLOR_GREEN, COLOR_RESET

SOCKET_TIMEOUT = 10  # 10 sec
# Значения из спецификации.
HANDSHAKE_HEADER = b'\x13BitTorrent protocol\0\0\0\0\0\0\0\0'
BLOCK_LEN = 2**14  # 16 KB

MSG_INTERESTED = 2
MSG_REQUEST = 6
MSG_PIECE = 7

class Peer(ExponentialBackoffMixin):
    def __init__(self, peer_id, ip, port):
        super().__init__()
        self.peer_id = peer_id
        self.address = (ip, port)
        self.connected = False
        self.socket = None
    
    def handshake(self, info_hash, client_peer_id):
        print(f'Connecting to {self!r}')
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(SOCKET_TIMEOUT)
        self.socket.connect(self.address)

        # Посылаем рукопожатие и получаем ответ.
        self.socket.sendall(HANDSHAKE_HEADER + info_hash + client_peer_id)
        res = self.receive_bytes(len(HANDSHAKE_HEADER) + 40)
        
        if not self.check_handshake(info_hash, res):
            raise ConnectionError(f'{self}: Got an unexpected handshake: {res}')
        
        # Сообщаем о своей заинтересованности в кусках, имеющихся у пира.
        self.socket.sendall(struct.pack('>ib', 1, MSG_INTERESTED))
        
    def check_handshake(self, info_hash, res):
        if res[:20] != HANDSHAKE_HEADER[:20]:  # проверка соответствия протокола
            return False
        if res[28:48] != info_hash:
            return False
        return True
    
    def download_piece(self, piece):
        print(f'Downloading {piece}...')
        
        data = bytes()
        offset = 0
        piece_len = piece.end - piece.start
        
        # Загружаем кусок по блокам.
        while offset < piece_len:
            block_len = min(BLOCK_LEN, piece_len - offset)
            # Запрос на очередной блок.
            self.socket.sendall(struct.pack('>ibiii', 13, MSG_REQUEST, piece.idx, offset, block_len))
            
            msg_len = struct.unpack('>I', self.receive_bytes(4))[0]
            msg = self.receive_bytes(msg_len)
            
            # Если пришло сообщение с нужным блоком - принять его.
            if msg_len > 9 and msg[:9] == struct.pack('>bii', MSG_PIECE, piece.idx, offset):
                offset += msg_len - 9
                data += msg[9:]
                
        print(f'Downloading {COLOR_GREEN}{piece}{COLOR_RESET} completed!')
        return data

    def receive_bytes(self, num_bytes):
        # Эффективный алгоритм получения нужного числа байт из сокета.
        # (Метод socket.recv(len) может вернуть меньше, чем len байт.)

        buf = bytearray(num_bytes)
        view = memoryview(buf)
        offset = 0
        while offset < num_bytes:
            offset += self.socket.recv_into(view[offset:])
        return buf

    def __str__(self):
        return f'{self.address[0]}:{self.address[1]}'

    def __repr__(self):
        return f'{self} ({self.peer_id})'
