


class RingRange:
    def __init__(self, module):
        self.module = module

    def in_range(self, first_value, second_value, check_value):
        if first_value > second_value:
            second_value += self.module
        if check_value < first_value:
            check_value += self.module

        return first_value < check_value < second_value

def tests():
    by_mod = 16
    r_s = RingRange(by_mod)


    assert r_s.in_range(2, 4, 3) == True
    assert r_s.in_range(4, 6, 7) == False
    assert r_s.in_range(4, 6, 4) == False
    assert r_s.in_range(4, 6, 6) == False
    assert r_s.in_range(6, 1, 0) == True
    assert r_s.in_range(2, 0, 1) == False
    assert r_s.in_range(0, 2, 1) == True
    assert r_s.in_range(0, 0, 0) == False
    assert r_s.in_range(0, 0, 3) == False
    assert r_s.in_range(6, 3, 0) == True
    assert r_s.in_range(6, 1, 8) == True

if __name__ == '__main__':
    tests()