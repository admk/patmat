"""
.. pakage:: patmat
    :synopsis: Functional programming style pattern matching in Python.
"""
__version__ = '1.0.1'
__author__ = 'Xitong Gao'
__email__ = '@'.join(['gxtfmx', 'gmail.com'])
__license__ = 'MIT'


from patmat.mimic import (
    Val, ZeroFsGiven, _, Type, Attr, Seq, List, Tuple, Dict, Mimic,
)
from patmat.match import Match, Switch, case
