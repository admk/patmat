_dummy = object()


class _Mimic(object):
    """A base class for all classes that mimic values of some Python objects.

    Subclasses must override :member:`_match` and :member:`__hash__`.
    """
    def _match_item(self, mimic, value, env):
        sub_env = {}
        if isinstance(mimic, _Mimic):
            value_match = mimic._match(value, sub_env)
            if not value_match:
                return False
        elif mimic != value:
            return False
        env.update(sub_env)
        return True

    def _match(self, other, env=None):
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

    def __hash__(self):
        raise NotImplementedError


class Val(_Mimic):
    """Mimics any object.

    All found matches will be given in the returned dictionary of
    :member:`match`.
    """
    def __init__(self, name=None):
        super(Val, self).__init__()
        self.name = name

    def _match(self, other, env=None):
        if env is not None:
            if self.name in env:
                raise ValueError(
                    'Name collision, {!r} already declared.'.format(self.name))
            if isinstance(other, _Mimic):
                raise ValueError(
                    'A Mimic instance {} exists in the value to be '
                    'matched.'.format(other))
            env[self.name] = other
        return True

    def __hash__(self):
        return hash((self.__class__, self.name))

    def __str__(self):
        return '{cls}({name!r})'.format(
            cls=self.__class__.__name__, name=self.name)
    __repr__ = __str__


class ZeroFsGiven(_Mimic):
    """Don't care, matches everything.  """
    def _match(self, other, env):
        return True

    def __hash__(self):
        return hash(self.__class__)

    def __str__(self):
        return '{cls}()'.format(cls=self.__class__.__name__)
    __repr__ = __str__
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

    def _match(self, other, env=None):
        if not isinstance(other, self.type):
            return False
        return self.mimic._match(other, env)

    def __hash__(self):
        return hash((self.__class__, self.type, self.mimic))

    def __str__(self):
        return '{cls}({type!r}, {mimic!r})'.format(
            cls=self.__class__.__name__,
            type=self.type.__name__, mimic=self.mimic)
    __repr__ = __str__


class Attr(_Mimic):
    """Mimics any objects with some attributes provided in `kwargs`.  """
    def __init__(self, **kwargs):
        super(Attr, self).__init__()
        self.attrs = kwargs

    def _match(self, other, env=None):
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

    def __str__(self):
        attrs = ', '.join('{k}={v!r}'.format(k=k, v=v)
                          for k, v in self.attrs.items())
        return '{cls}({attrs})'.format(
            cls=self.__class__.__name__, attrs=attrs)
    __repr__ = __str__


class Seq(_Mimic):
    """Mimics a sequence of objects.  """
    def __init__(self, sequence):
        super(Seq, self).__init__()
        self.seq = tuple(sequence)

    def _match(self, other, env=None):
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

    def __str__(self):
        return '{cls}({seq!r})'.format(
            cls=self.__class__.__name__, seq=self.seq)
    __repr__ = __str__


class _TypedSeq(Type):
    """Mimics a sequence of a particular type, of objects.  """
    type = None

    def __init__(self, seq):
        super(_TypedSeq, self).__init__(self.type, Seq(seq))

    def __str__(self):
        return '{cls}({seq!r})'.format(
            cls=self.__class__.__name__, seq=self.mimic.seq)
    __repr__ = __str__


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

    def __str__(self):
        attrs = ', '.join('{k!r}: {v!r}'.format(k=k, v=v)
                          for k, v in self.dictionary.items())
        return '{cls}({{{attrs}}})'.format(
            cls=self.__class__.__name__, attrs=attrs)
    __repr__ = __str__


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
    return value
