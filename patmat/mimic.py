_dummy = object()


class _Mimic(object):
    """A base class for all classes that mimic values of some Python objects.

    Subclasses must override :member:`_match` and :member:`__hash__`.
    """
    def _match_item(self, mimic, value, env):
        sub_env = dict(env)
        if isinstance(mimic, _Mimic):
            value_match = mimic._match(value, sub_env)
            if not value_match:
                return False
        elif mimic != value:
            return False
        env.update(sub_env)
        return True

    def _match(self, other, env):
        raise NotImplementedError

    def match(self, other):
        env = {}
        if self._match(other, env):
            return env
        return None

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return vars(self) == vars(other)

    def __or__(self, other):
        return Or(self, other)

    def __hash__(self):
        raise NotImplementedError
mimic_type = _Mimic


class Val(_Mimic):
    """Mimics any object.

    All found matches will be given in the returned dictionary of
    :member:`match`.
    """
    def __init__(self, name=None):
        super(Val, self).__init__()
        self.name = name

    def _match(self, other, env):
        value = env.get(self.name, _dummy)
        if value is not _dummy:
            return self._match_item(value, other, env)
        if isinstance(other, _Mimic):
            raise ValueError(
                'A Mimic instance {} exists in the value to be '
                'matched.'.format(other))
        env[self.name] = other
        return True

    def __hash__(self):
        return hash((self.__class__, self.name))

    def __repr__(self):
        return '{cls}({name!r})'.format(
            cls=self.__class__.__name__, name=self.name)


class ZeroFsGiven(_Mimic):
    """Don't care, matches everything.  """
    def _match(self, other, env):
        return True

    def __hash__(self):
        return hash(self.__class__)

    def __repr__(self):
        return '{cls}()'.format(cls=self.__class__.__name__)
_ = ZeroFsGiven


class Type(_Mimic):
    """Mimics any objects with a given type.

    :param type: The type of the object to be matched.
    :param mimic: A mimic instance which requires the contents to be matched.
    """
    def __init__(self, type, mimic=ZeroFsGiven()):
        super(Type, self).__init__()
        self.type = type
        self.mimic = mimic

    def _match(self, other, env):
        if not isinstance(other, self.type):
            return False
        return self.mimic._match(other, env)

    def __hash__(self):
        return hash((self.__class__, self.type, self.mimic))

    def __repr__(self):
        return '{cls}({type}, {mimic!r})'.format(
            cls=self.__class__.__name__, type=self.type, mimic=self.mimic)


class Attr(_Mimic):
    """Mimics any objects with some attributes provided in `kwargs`.  """
    def __init__(self, **kwargs):
        super(Attr, self).__init__()
        self.attrs = kwargs

    def _match(self, other, env):
        for attr, attr_value in self.attrs.items():
            try:
                other_value = getattr(other, attr)
            except AttributeError:
                return False
            if not self._match_item(attr_value, other_value, env):
                return False
        return True

    def __hash__(self):
        return hash((self.__class__, self.attrs))

    def __repr__(self):
        attrs = ', '.join('{k}={v!r}'.format(k=k, v=v)
                          for k, v in self.attrs.items())
        return '{cls}({attrs})'.format(
            cls=self.__class__.__name__, attrs=attrs)


class Seq(_Mimic):
    """Mimics a sequence of objects.  """
    def __init__(self, sequence):
        super(Seq, self).__init__()
        self.seq = tuple(sequence)

    def _match(self, other, env):
        index = other_index = 0
        while index < len(self.seq):
            if self.seq[index] is Ellipsis:
                index += 1
                # end of sequence, '...' matches anything
                if index == len(self.seq):
                    return True
                item = self.seq[index]
                if isinstance(item, Val):
                    raise ValueError(
                        'Val instance cannot be immediately after "..."')
                # [......, Ellipsis, something, ......]
                # matches something in the middle
                while other_index < len(other):
                    if self._match_item(item, other[other_index], env):
                        break
                    other_index += 1
                else:
                    return False
            else:
                if other_index >= len(other):
                    return False
                item_matched = self._match_item(
                    self.seq[index], other[other_index], env)
                if not item_matched:
                    return False
            index += 1
            other_index += 1
        if other_index != len(other):
            # did not finish matching
            return False
        return True

    def __hash__(self):
        return hash((self.__class__, self.seq))

    def __repr__(self):
        return '{cls}({seq!r})'.format(
            cls=self.__class__.__name__, seq=self.seq)


class _TypedSeq(Type):
    """Mimics a sequence of a particular type, of objects.  """
    type = None

    def __init__(self, seq):
        super(_TypedSeq, self).__init__(self.type, Seq(seq))

    def __repr__(self):
        return '{cls}({seq!r})'.format(
            cls=self.__class__.__name__, seq=self.mimic.seq)


class List(_TypedSeq):
    """Mimics a list.  """
    type = list


class Tuple(_TypedSeq):
    """Mimics a tuple.  """
    type = tuple


class Dict(_Mimic):
    """Mimics a dictionary.

    Either keys or values can be recusively matched.
    """
    def __init__(self, dictionary=None, **kwargs):
        super(Dict, self).__init__()
        self.dictionary = dictionary or {}
        self.dictionary.update(kwargs)

    def _match(self, other, env):
        other = dict(other)
        for key, value in self.dictionary.items():
            for okey, ovalue in dict(other).items():
                if self._match_item(key, okey, env) and \
                   self._match_item(value, ovalue, env):
                    del other[okey]
                    break
            else:
                return False
        return True

    def __hash__(self):
        return hash((self.__class__, tuple(self.dictionary.items())))

    def __repr__(self):
        attrs = ', '.join('{k!r}: {v!r}'.format(k=k, v=v)
                          for k, v in self.dictionary.items())
        return '{cls}({{{attrs}}})'.format(
            cls=self.__class__.__name__, attrs=attrs)


class Or(_Mimic):
    """Mimics if at least one of args is matching"""

    def __init__(self, *args):
        super(Or, self).__init__()
        self.args = [Mimic(arg) for arg in args]

    def _match(self, other, env):
        for mimic in self.args:
            if isinstance(mimic, _Mimic):
                sub_env = dict(env)
                value_match = mimic._match(other, sub_env)
                if value_match:
                    env.update(sub_env)
                    return True
            elif mimic == other:
                return True

        return False

    def __repr__(self):
        attrs = ', '.join(repr(mimic)
                          for mimic in self.args)
        return '{cls}({attrs})'.format(
            cls=self.__class__.__name__, attrs=attrs)

    def __hash__(self):
        return hash((self.__class__, tuple(self.args)))


class Pred(_Mimic):
    """Mimics something satisfying a predicate.  """
    def __init__(self, predicate, mimic=ZeroFsGiven()):
        super(Pred, self).__init__()
        self.predicate = predicate
        self.mimic = mimic

    def _match(self, other, env):
        if not self.predicate(other):
            return False
        return self.mimic._match(other, env)

    def __hash__(self):
        return hash((self.__class__, self.predicate, self.mimic))

    def __repr__(self):
        return '{cls}({predicate}, {mimic!r})'.format(
            cls=self.__class__.__name__,
            predicate=self.predicate, mimic=self.mimic)


def Mimic(*args, **kwargs):
    """Lazy programmer's stuff.

    Automatically determines the correct mimic instances from definition.
    """
    if kwargs:
        if args:
            raise ValueError('Attribute matching should not take a sequence.')
        for k, v in kwargs.items():
            kwargs[k] = Mimic(v)
        return Attr(**kwargs)
    if len(args) > 1:
        return Seq(args)
    value = args[0]
    if isinstance(value, type):
        return Type(value)
    if isinstance(value, list):
        return List(Mimic(v) for v in value)
    if isinstance(value, tuple):
        return Tuple(Mimic(v) for v in value)
    if isinstance(value, dict):
        return Dict({Mimic(k): Mimic(v) for k, v in value.items()})
    if callable(value):
        return Pred(value)
    return value
