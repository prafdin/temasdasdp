from ring_range import RingRange


def in_circle_range(key, start, end):
    return ring_range.in_range(start, end, key)

class Finger:
    def __init__(self, node, i):
        self.start = (node.id + 2**i) % M
        self.end = (node.id + 2**(i+1)) % M
        self.interval = range(self.start, self.end)
        self.node = node

    def __str__(self):
        return f"node:{self.node};int:[{self.start}, {self.end})"


class ChordNode:
    def __init__(self, id):
        self.id = id
        self.predecessor = self
        self.fingers = [Finger(self, i) for i in range(m)]

    def join(self, another_node):
        self.init_finger_table(another_node)
        self.update_others(another_node)

    def init_finger_table(self, another_node):
        self.set_successor(another_node.find_successor(self.fingers[1].start))
        self.predecessor = self.get_successor().predecessor
        self.get_successor().predecessor = self

        f = self.fingers
        for i in range(1, m - 1):
            if in_circle_range(f[i + 1].start, self.id - 1, f[i].node.id):
                self.fingers[i + 1].node = f[i].node
            else:
                successor_from_another_node = another_node.find_successor(f[i + 1].start)
                self.fingers[i + 1].node = successor_from_another_node

    def update_fingers(self, n, i):
        if (self.id == 0 and self.fingers[i].node.id == 0) or in_circle_range(n.id, self.id - 1, self.fingers[i].node.id):
            self.fingers[i].node = n
            p = self.predecessor
            if p != n:
                self.predecessor.update_fingers(n, i)

    def update_others(self, another_node):
        for i in range(1, m):
            p = another_node.find_predecessor(self.id- 2 **(i-1))

            p.update_fingers(self, i)

    def find_successor(self, node_id):
        predecessor = self.find_predecessor(node_id)
        return predecessor.get_successor()

    def find_predecessor(self, node_id):
        n = self
        iteration_count = 0
        while not in_circle_range(node_id, n.id, n.get_successor().id + 1):
            if iteration_count == M:
                return n
            n = n.closest_preceding_finger(node_id)

            iteration_count += 1

        return n

    def closest_preceding_finger(self, key):
        """
        Called only from find_predecessor(..., node_id) function
        Finds the nearest node to node_id in fingers table of current node
        If found nothing then looks like the nearest node is it
        """
        for f in reversed(self.fingers[1:]):
            if in_circle_range(f.node.id, self.id, key):
                return f.node
        return self

    def get_successor(self):
        return self.fingers[1].node

    def set_successor(self, new_successor):
        self.fingers[1].node = new_successor


m = 4  # GUID in bit
M = 2**m  # Max nodes count
ring_range = RingRange(M)

def tests():
    ch0 = ChordNode(0)
    ch6 = ChordNode(6)
    ch8 = ChordNode(8)
    ch3 = ChordNode(3)

    ch6.join(ch0)
    # ch8.join(ch0)

    assert ch0.find_successor(3).id == 6
    assert ch0.find_successor(6).id == 6
    assert ch6.find_successor(3).id == 6
    assert ch6.find_successor(6).id == 0
    assert ch6.find_successor(8).id == 0
    assert ch0.find_successor(8).id == 0
    assert ch0.find_successor(5).id == 6
    assert ch6.find_successor(5).id == 6
    assert ch0.find_successor(0).id == 6
    assert ch0.find_successor(15).id == 0

    ch8.join(ch0)
    assert ch0.find_successor(7).id == 8
    assert ch0.find_successor(9).id == 0

    ch3.join(ch0)
    assert ch0.find_successor(2).id == 3
    assert ch0.find_successor(4).id == 6

if __name__ == '__main__':
    tests()