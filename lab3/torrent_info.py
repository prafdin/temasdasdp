import pprint

from helpers import Piece, File, bencode, get_hash

class TorrentInfo:
    def __init__(self, filename):
        with open(filename, 'rb') as f:
            data = f.read()
        data = bencode.decode(data)
        self.raw_data = data
        
        self.announce = data['announce']  
        self.info = data['info']
        self.piece_length = self.info['piece length']
        self.info_hash = get_hash(bencode.encode(self.info))

        
        
        flat_trackers = sum(data.get('announce-list', []), [])
        self.trackers = set(flat_trackers)
        self.trackers.add(self.announce)
        
        self.init_files()
        self.init_pieces()
    
    def init_files(self):
        self.files = []
        self.size = 0
        
        
        if 'length' in self.info:
            self.info['files'] = [{
                'length': self.info['length'],
                'path': [],
            }]
        
        name = self.info['name']
        for f in self.info['files']:
            file = File(self.size, self.size + f['length'], name, *f['path'])
            self.files.append(file)
            self.size += f['length']
    
    def init_pieces(self):
        self.pieces = []
        file_idx = 0

        piece_hashes = self.info['pieces']
        if isinstance(piece_hashes, str):
            piece_hashes = bytes(piece_hashes, encoding='utf-8')
        
        
        for piece_idx in range(len(piece_hashes) // 20):
            piece_start = piece_idx * self.piece_length
            piece_end = min(piece_start + self.piece_length, self.size)
            hash_start = piece_idx * 20
            piece_hash = piece_hashes[hash_start:hash_start+20]

            p = Piece(piece_idx, piece_start, piece_end, piece_hash)
            self.pieces.append(p)
            
            
            p.start_file_idx = file_idx
            while file_idx < len(self.files):
                if self.files[file_idx].end >= piece_end:
                    
                    
                    p.end_file_idx = file_idx + 1
                    break

                
                file_idx += 1

    def __str__(self):
        repr = self.raw_data.copy()
        repr['info'] = self.info.copy()
        repr['info'].pop('pieces')  
        repr['info_hash'] = self.info_hash.hex()
        repr['size'] = self.size
        repr['piece_count'] = len(self.pieces)
        return pprint.pformat(repr)  
                