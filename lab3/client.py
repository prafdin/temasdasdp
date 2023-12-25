import random
import threading

from helpers import get_hash
from torrent_info import TorrentInfo
from tracker import TrackerConnector
from worker import Worker

NUM_WORKERS = 8

class TorrentClient:
    
    def __init__(self, filename):
        self.ti = TorrentInfo(filename)
        self.peer_id = random.randbytes(20).hex()

        self.uploaded = self.downloaded = 0
        
        self.num_active_workers = 0

        self.peers = {}
        self.piece_queue = []


        self.cv_peers = threading.Condition()
        self.cv_pieces = threading.Condition()
        self.maybe_done = threading.Event()

    @property
    def left(self):
        
        return len(self.piece_queue) * self.ti.piece_length
        
    def start(self):
        
        

        for announce_url in self.ti.trackers:
            connector = TrackerConnector(self, announce_url)
            threading.Thread(target=connector.start, daemon=True).start()

        for _ in range(NUM_WORKERS):
            w = Worker(self)
            threading.Thread(target=w.start, daemon=True).start()
            
        self.check_and_download()
            
        
        while self.piece_queue or self.num_active_workers > 0:
            self.maybe_done.wait()
            self.maybe_done.clear()

        self.check_all()
    
    def check_and_download(self):
        for p in self.ti.pieces:
            if not self.check_piece(p):
                self.queue_piece_for_download(p)
            else:
                print(f'Have piece #{p.idx}')
    
    def check_all(self):
        print()
        for p in self.ti.pieces:
            if not self.check_piece(p):
                print(f'Bad {p}. Download incomplete :((')
                break
        else:
            print('All pieces checked! Download completed successfully.')
 
    def check_piece(self, p):
        
        piece = bytes()
        for f in self.ti.files[p.start_file_idx:p.end_file_idx]:
            chunk = f.read(p.start, p.end)
            if chunk is None:
                
                return False
            piece += chunk
            
        
        return get_hash(piece) == p.sha1
    
    def queue_piece_for_download(self, p):
        with self.cv_pieces:
            self.piece_queue.insert(0, p)  
            
            self.cv_pieces.notify()
