import random

from helpers import get_hash, log_error

class Worker:
    def __init__(self, cl):
        self.cl = cl
        # Пир, к которому этот воркер подключен в данный момент.
        self.peer = None
        
    def start(self):
        while True:
            try:
                new_peer = self.get_peer()
                if new_peer != self.peer:
                    self.peer = new_peer
                    self.peer.handshake(self.cl.ti.info_hash, self.cl.peer_id)
                    
                piece = self.get_piece()
                self.download_piece(piece)
                self.peer.success()
            except Exception as e:
                self.peer.fail()
                log_error(self.peer, e)
                self.close()
                
    def get_peer(self):
        with self.cl.cv_peers:
            # Текущий пир всё ещё в списке доступных, оставляем его.
            if self.peer and self.peer.active:
                return self.peer
            
            # Разрываем соединение с текущим пиром.
            self.close()
            
            while True:
                # Получаем список всех пиров в случайном порядке.
                peers = list(self.cl.peers.values())
                random.shuffle(peers)

                for p in peers:
                    # Игнорируем тех, у кого идёт ожидание после ошибки и тех,
                    # к кому уже подключен другой воркер.
                    if p.active and not p.connected:
                        p.connected = True
                        return p

                # Свободных пиров не нашлось.
                # Ждём, пока другой поток обновит их и разбудит нас.
                # Просыпаемся раз в 10 секунд, чтобы проверить, не появились
                # ли пиры, у которых истекло время ожидания после ошибки.
                self.cl.cv_peers.wait(timeout=10)
                
    def get_piece(self):
        with self.cl.cv_pieces:
            while True:
                if self.cl.piece_queue:
                    # Достаём кусок из очереди.
                    return self.cl.piece_queue.pop()

                # Свободных кусков не нашлось.
                # Ждём, пока другой поток обновит их и разбудит нас.
                self.cl.cv_pieces.wait()
                
    def download_piece(self, piece):
        self.cl.num_active_workers += 1
        try:
            data = self.peer.download_piece(piece)
            if get_hash(data) != piece.sha1:
                raise ValueErrror(f'Got {piece} with non-matching hash!')
            self.write_to_disk(piece, data)
            self.cl.downloaded += len(data)
        except:
            # Не удалось загрузить кусок, возвращаем его в очередь
            # и кидаем ошибку дальше.
            self.cl.queue_piece_for_download(piece)
            raise
        finally:
            # Цикл активности завершён (неважно, удачно или нет).
            self.cl.num_active_workers -= 1
            # Будим поток, который проверяет, остались ли ещё активные воркеры.
            if not self.cl.piece_queue:
                self.cl.maybe_done.set()
        
    def write_to_disk(self, piece, data):
        # Записываем соответствующую часть куска в каждый из пересекающихся файлов.
        for f in self.cl.ti.files[piece.start_file_idx:piece.end_file_idx]:
            f.write(piece.start, piece.end, data)
            
    def close(self):
        if self.peer is not None:
            self.peer.connected = False
            if self.peer.socket is not None:
                self.peer.socket.close()
            self.peer = None 
