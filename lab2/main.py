import random
from chord_node import ChordNode

m = 4 # GUID space size in bit
M = 2 ** m


def main():
    nodes = [ChordNode(i) for i in range(M)]

    first_node = nodes[0]
    for n in nodes[1:]:
        n.join(first_node)

    first_node.put_obj(2, "ABC")
    ch2 = nodes[2]
    ch2.leave_network()

    print(nodes[random.randint(0, M-1)].get_obj(2))



if __name__ == '__main__':
    main()