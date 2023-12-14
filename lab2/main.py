import random

m = 3 # GUID space size in bit
M = 2 ** m
import hashlib

def get_key(data):
    if not isinstance(data, bytes):
        data = str(data).encode("utf-8")
    hash = hashlib.sha1(data).digest()
    return int.from_bytes(hash[:m // 8], "big")


def is_in_range(key, start, end):
    start %= M
    end %= M

    if end <= start:
        end += M
    if key < start:
        key += M

    return start <= key < end


class Finger:
    def __init__(self, node, i):
        self.start = (node.key + 2**i) % M
        self.node = node

class ChordNode:
    def __init__(self, id):
        self.key = id
        # self.objects = {}

        self.fingers = [Finger(self, i) for i in range(m)]
        self.predecessor = self
        # self.ring_id = random.randint(1, M)

    def join(self, node_in_network):
        f = self.fingers
        self.successor = node_in_network.find_successor(f[0].start)
        self.predecessor = self.successor.predecessor

        # init fingers
        for i in range(0, m - 1):
            if is_in_range(f[i + 1].start, self.key, f[i].node.key):
                f[i + 1].node = f[i].node
            else:
                f[i + 1].node = node_in_network.find_successor(f[i + 1].start)

        # update_others
        for i in range(m):
            p = self.find_predecessor(self.key - 2 ** i)
            p.update_fingers(self, i)

    def find_successor(self, key):
        return self.find_predecessor(key).successor

    def find_predecessor(self, key):
        n = self
        i = m * 2

        while not is_in_range(key, n.key + 1, n.successor.key + 1):
            if not i:
                raise Exception("Predecessor lookup too long!")
            n = n.closest_preceding_finger(key)
            i -= 1

        return n

    def closest_preceding_finger(self, key):
        for f in reversed(self.fingers):
            if is_in_range(f.node.key, self.key + 1, key):
                return f.node
        assert False, "Can't find preceding finger"

    def update_fingers(self, n, i):
        if is_in_range(n.key, self.key + 1, self.fingers[i].node.key):
            self.fingers[i].node = n
            self.predecessor.update_fingers(n, i)

    @property
    def successor(self):
        return self.fingers[0].node

    @successor.setter
    def successor(self, value):
        self.fingers[0].node = value

    #
    # def get_object(self, key):
    #     pred = self.find_predecessor(key)
    #     succ = pred.get_successor()
    #     return pred.fetch_object(key) or succ.fetch_object(key)
    #
    # def fetch_object(self, key):
    #     return self.objects.get(key)
    #
    # def put_object(self, key, obj):
    #     pred = self.find_predecessor(key)
    #     pred.store_object(key, obj)
    #     pred.get_successor().store_object(key, obj)
    #
    # def store_object(self, key, obj):
    #     self.objects[key] = obj
    #
    # def request_objects(self, n, forward):
    #     if forward:
    #         start, end = self.key + 1, n.key + 1
    #     else:
    #         start, end = n.key + 1, self.key + 1
    #
    #     objects = dict(n.serve_objects(start, end))
    #     new_keys = set(objects.keys()) - set(self.objects.keys())
    #     if new_keys:
    #         self.print(f"Got {list(new_keys)} from {n}")
    #         self.objects |= objects
    #
    # def serve_objects(self, start, end):
    #     objects = {k: v for k, v in self.objects.items() if is_in_range(k, start, end)}
    #
    #     # prune redundant objects
    #     for k in list(self.objects.keys()):
    #         if not is_in_range(k, self.predecessor.key + 1, self.successor.key + 1):
    #             self.print(f"Pruning object {k}")
    #             self.objects.pop(k)
    #
    #     return tuple(objects.items())
    #
    # # method group: UTILITY METHODS
    #
    # def register_remote(self, node):
    #     if isinstance(node, network.RemoteNode):
    #         node.master = self
    #         return self.remotes.setdefault(node.address, node)
    #     return node
    #


def main():
    max_nodes_count = 2**m

    nodes_list = [None] * max_nodes_count

    print(nodes_list)
    ch0 = ChordNode(0)
    ch1 = ChordNode(1)
    ch3 = ChordNode(3)

    ch1.join(ch0)
    ch3.join(ch0)
    print("asd")




if __name__ == '__main__':
    main()