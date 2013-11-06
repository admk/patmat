try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

from patmat.mimic import Mimic


class Match(object):
    def __init__(self, *match_rules):
        self.rules = match_rules

    def with_value(self, *args):
        def _match(value):
            for matcher, func in self.rules:
                match_dict = matcher.match(value)
                if not match_dict:
                    continue
                func = func or True
                yield func(**match_dict) if callable(func) else func
        value_list = []
        for value in args:
            value_list += _match(value)
        if len(value_list) == 1:
            return value_list[0]
        return value_list


class Switch(object):
    def __init__(self, *args):
        self.values = args

    def with_case(self, mimic, func=None):
        func = func or True
        value_list = []
        for v in self.values:
            match_dict = mimic.match(v)
            if not match_dict:
                continue
            value_list.append(func(**match_dict) if callable(func) else func)
        if len(value_list) == 1:
            return value_list[0]
        return value_list


class FunctionNotMatched(Exception):
    """Function is unmatched.  """


class _DotDict(dict):
    def __init__(self, dictionary, **kwargs):
        dictionary = dict(dictionary, **kwargs)
        super(_DotDict, self).__init__(dictionary)
        self.__dict__.update(dictionary)


class Dispatcher(object):
    def __init__(self):
        self.func_map = {}

    def __call__(self, func):
        arg_defaults = func.__defaults__ or tuple()
        arg_names = func.__code__.co_varnames[1:]
        if len(arg_names) != len(arg_defaults):
            raise SyntaxError('Each argument must have a default value.')
        if not arg_names:  # no arguments
            return func
        arg_sig = {k: v for k, v in zip(arg_names, arg_defaults)}
        func_name = func.__code__.co_name
        func_list = self.func_map.setdefault(func_name, [])
        func_list.append((func, Mimic(arg_sig)))

        def wrapper(*args, **kwargs):
            conc_sig = {k: v for k, v in zip_longest(arg_names, args)}
            conc_sig.update(kwargs)
            for k, v in conc_sig.items():
                if v is None:
                    conc_sig[k] = arg_sig[k]
            for func, abs_sig in self.func_map[func_name]:
                match_env = abs_sig.match(conc_sig)
                if match_env is None:
                    continue
                return func(_DotDict(match_env), *args, **kwargs)
            sig = ', '.join('{}={!r}'.format(k, v)
                            for k, v in conc_sig.items())
            raise FunctionNotMatched(
                "Function call {func}({sig}) cannot be matched.".format(
                    func=func_name, sig=sig))
        return wrapper


case = Dispatcher()
