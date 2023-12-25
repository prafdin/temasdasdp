import hashlib
from pathlib import Path
import threading
import time

from bencodepy import Bencode

bencode = Bencode(encoding='utf-8', encoding_fallback='all')
print_lock = threading.Lock()

COLOR_RED = '\033[31m'
COLOR_GREEN = '\033[32m'
COLOR_RESET = '\033[0m'

def get_hash(data):
    return hashlib.sha1(data).digest()

def log_error(obj, e):
    with print_lock:
        print()
        print(f'{obj}: {COLOR_RED}{type(e).__name__}{COLOR_RESET}: {e}')
        if isinstance(obj, ExponentialBackoffMixin):
            print(f'Next attempt after {obj.backoff_sec} s')
        print()
    
            
            
class Piece:
    def __init__(self, idx, start, end, sha1):
        self.idx = idx
        self.start = start
        self.end = end
        self.sha1 = sha1
        
        self.start_file_idx = self.end_file_idx = None

    def __str__(self):
        return f'piece#{self.idx}'


class File:
    def __init__(self, start, end, *path_segments):
        self.start = start
        self.end = end
        self.path = Path(*path_segments)
        
    def read(self, pstart, pend):
        
        start = max(pstart, self.start)
        end = min(pend, self.end)
        
        try:
            with self.path.open("rb") as f:
                
                
                
                f.seek(start - self.start)
                return f.read(end - start)  
        except OSError as e:
            
            return None
        
    def write(self, pstart, pend, data):
        start = max(pstart, self.start)
        end = min(pend, self.end)
        data = data[start - pstart : end - pstart]
        
        
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch()
        with self.path.open("r+b") as f:
            f.seek(start - self.start)
            f.write(data)





class ExponentialBackoffMixin:
    BACKOFF_MULTIPLIER = 15
    MAX_FAILURES = 10

    def __init__(self):
        self.num_failures = 0
        self.sleep_until = time.monotonic()

    @property
    def active(self):
        return time.monotonic() >= self.sleep_until

    @property
    def backoff_sec(self):
        if self.num_failures == 0:
            return 0
        return self.BACKOFF_MULTIPLIER * 2**(self.num_failures - 1)

    def fail(self):
        self.num_failures = min(self.num_failures + 1, self.MAX_FAILURES)
        backoff = self.backoff_sec
        self.sleep_until = time.monotonic() + backoff
        return backoff

    def success(self):
        self.num_failures = 0

    def sleep(self):
        if (length := self.sleep_until - time.monotonic()) > 0:
            time.sleep(length)
