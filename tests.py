import unittest

from patmat import (
    Val, ZeroFsGiven, Attr, Seq, List, Tuple, Dict, Type, Mimic, Or,
    Match, Switch, case
)


class TestMimic(unittest.TestCase):
    def test_type_matching(self):
        for v in [Val('a'), Type(int, Val('a'))]:
            self.assertEqual(v.match(1), {'a': 1})
        self.assertFalse(Type(float, Val('a')).match(1))

    def test_attribute_matching(self):
        class SomeClass(object):
            __init__ = lambda self, **kwargs: self.__dict__.update(kwargs)
        m = Attr(a=Val('a'), b=Attr(c=Val('c')))
        c = SomeClass(a=1, b=SomeClass(c=2))
        self.assertEqual(m.match(c), {'a': 1, 'c': 2})

    def test_sequence_matching(self):
        m = Seq([Val('a'), 1, Ellipsis, 3, Val('b')])
        self.assertEqual(m.match(range(5)), {'a': 0, 'b': 4})

    def test_dictionary_matching(self):
        m = Dict({
            1: Val('a'), Val('b'): 4,
            Tuple([Val('c'), 6]): Tuple([7, Val('d')])
        })
        d = {1: 2, 3: 4, (5, 6): (7, 8)}
        self.assertEqual(m.match(d), {'a': 2, 'b': 3, 'c': 5, 'd': 8})

    def test_or_matching(self):
        cases = (
            (Or('a', 'b'), 'a', {}),
            (Or('a', 'b', Val('x')), 'c', {'x': 'c'}),
            (Or('a', 'b', Val('x')), 'a', {}),
            (Mimic({'a': Or('x', 'y')}), {'a': 'z'}, None),
            (Mimic({'a': Or('x', 'y')}), {'a': 'x'}, {}),
            (Mimic(['x']) | Mimic(['y']) | Mimic(['z']), ['z'], {}),
            (Or([Val('x'), 'a'], [Val('y'), 'b']), [1, 'b'], {'y': 1}),
        )
        for m, obj, expected in cases:
            self.assertEqual(m.match(obj), expected)

    def test_zero_fs_matching(self):
        m = ZeroFsGiven()
        self.assertEqual(m.match(1), {})

    def test_mimic(self):
        m = Mimic([
            1, 2, Mimic(a=3, b=[4, Val(5), 6], c=Val(7)),
            Val(8), {Val(9): 10, Val(11): 12},
        ])
        n = List([
            1, 2, Attr(a=3, b=List([4, Val(5), 6]), c=Val(7)),
            Val(8), Dict({Val(9): 10, Val(11): 12}),
        ])
        self.assertEqual(m, n)

    def test_repr(self):
        cases = (
            (Or('a', {'x': 5}, 'c'), "Or('a', Dict({'x': 5}), 'c')"),
        )
        for mimic, expected in cases:
            self.assertEqual(repr(mimic), expected)


class TestMatch(unittest.TestCase):
    def test_match_and_switch(self):
        m = Match([Val('a'), lambda a: a])
        self.assertEqual(m.with_value(1), 1)
        s = Switch(1)
        self.assertEqual(s.with_case(Val('a'), lambda a: a), 1)

    def test_case_decorator_args(self):
        @case
        def func(matched, x=Val('x'), y=Val('y'), z=Val('z')):
            self.assertEqual(matched, {'x': 1, 'y': 2, 'z': 3})

        func(1, 2, 3)
        func(1, 2, z=3)
        func(*[1, 2], z=3)
        func(1, y=2, z=3)
        func(x=1, y=2, z=3)

    def test_case_decorator_dispatch(self):
        @case
        def func(match, x=int):
            print('Do something with an integer.')

        @case
        def func(match, x=float):
            print('Do something with a float.')

        func(1)
        func(1.0)
