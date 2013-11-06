patmat
======

Functional-style recursive pattern matching in Python. Crazy stuff.


Install
-------
.. code-block:: sh

    pip install patmat


Usage
-----

Pattern matching with `patmat`:

.. code-block:: python

    >>> from patmat import *
    >>> Mimic({(1, Val('k')): (3, Val('v'))}).match({(1, 2): (3, 4)})
    {'k': 2, 'v': 4}

Multiple dispatch generic functions:

.. code-block:: python

    >>> from patmat import *
    >>>
    >>> @case
    >>> def func(match, l=[Val('head'), ..., 3, Val('tail')]):
    ...     print('a list with a head {} and a tail {}'.format(match.head, match.tail))
    >>>
    >>> @case
    >>> def func(match, l=Val('item')):
    ...     print('an item {}'.format(match.item))
    >>>
    >>> func([1, 2, 3, 4])
    a list with a head 1 and a tail 4
    >>> func(5)
    an item: 5

More dispatch examples:

.. code-block:: python

    >>> @case
    >>> def func(_, x=int):
    ...     print('Do something with an integer.')
    >>>
    >>> @case
    >>> def func(_, x=float):
    ...     print('Do something with a float.')
    >>>
    >>> func(1)
    Do something with an integer
    >>> func(1.0)
    Do something with a float

Matches ``list``, ``tuple``, ``dict``, types, classes with attributes. Brace
yourself for the power of recursive pattern matching:

.. code-block:: python

    >>> from patmat import *
    >>> m = Mimic([
    ...     1, Type(int, Val(2)),
    ...     Mimic(a=3, b=[4, Val(5), 6], c=Val(7)),
    ...     Val(8), {Val(9): 10, Val(11): 12},
    ... ])
    >>> class A: 
    ...     __init__ = lambda self, **kwargs: self.__dict__.update(kwargs)
    >>> m.match([1, 2, A(a=3, b=[4, 5, 6], c=7), 8, {9: 10, 11: 12}])
    {2: 2, 5: 5, 7: 7, 8: 8, 9: 9, 11: 11}
