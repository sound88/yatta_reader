
import collections
import operator
import re
import typing
from collections import Callable
from copy import copy, deepcopy
from itertools import chain
from numbers import Number
from typing import Optional

from serial import model


UNDEFINED = object()


class JSON(object):

    def __init__(
        self,
        types=None,  # type: Optional[Sequence[str]]
        formats=None,  # type: Optional[Sequence[str]]
    ):
        self.types = types
        self.formats = formats


class XML(object):

    def __init__(
        self,
    ):
        pass


_DOT_SYNTAX_RE = re.compile(
    r'^\d+(\.\d+)*$'
)


class Version(object):

    def __init__(
        self,
        _=None,  # type: Optional[str]
        specification=None,  # type: Optional[Sequence[str]]
        equals=None,  # type: Optional[Sequence[Union[str, Number]]]
        not_equals=None,  # type: Optional[Sequence[Union[str, Number]]]
        less_than=None,  # type: Optional[Sequence[Union[str, Number]]]
        less_than_or_equal_to=None,  # type: Optional[Sequence[Union[str, Number]]]
        greater_than=None,  # type: Optional[Sequence[Union[str, Number]]]
        greater_than_or_equal_to=None,  # type: Optional[Sequence[Union[str, Number]]]
        types=None,  # type: typing.Sequence[Union[type, Property]]
    ):
        if isinstance(_, str) and (
            (specification is None) and
            (equals is None) and
            (not_equals is None) and
            (less_than is None) and
            (less_than_or_equal_to is None) and
            (greater_than is None) and
            (greater_than_or_equal_to is None)
        ):
            specification = None
            for s in _.split('&'):
                if '==' in s:
                    s, equals = s.split('==')
                elif '<=' in s:
                    s, less_than_or_equal_to = s.split('<=')
                elif '>=' in s:
                    s, greater_than_or_equal_to = s.split('>=')
                elif '<' in s:
                    s, less_than = s.split('<')
                elif '>' in s:
                    s, greater_than = s.split('>')
                elif '!=' in s:
                    s, not_equals = s.split('!=')
                elif '=' in s:
                    s, equals = s.split('=')
                if specification:
                    if s != specification:
                        raise ValueError(
                            'Multiple specifications cannot be associated with an instance of ``serial.meta.Version``: ' +
                            repr(_)
                        )
                elif s:
                    specification = s
            self.specification = specification
        self.equals = equals
        self.not_equals = not_equals
        self.less_than = less_than
        self.less_than_or_equal_to = less_than_or_equal_to
        self.greater_than = greater_than
        self.greater_than_or_equal_to = greater_than_or_equal_to
        self.types = types

    def __eq__(self, other):
        # type: (Any) -> bool
        compare_properties_functions = (
            ('equals', operator.eq),
            ('not_equals', operator.ne),
            ('less_than', operator.lt),
            ('less_than_or_equal_to', operator.le),
            ('greater_than', operator.gt),
            ('greater_than_or_equal_to', operator.ge),
        )
        if isinstance(other, str) and _DOT_SYNTAX_RE.match(other):
            other_components = tuple(int(n) for n in other.split('.'))
            for compare_property, compare_function in compare_properties_functions:
                compare_value = getattr(self, compare_property)
                if compare_value is not None:
                    compare_values = tuple(int(n) for n in compare_value.split('.'))
                    other_values = copy(other_components)
                    ld = len(other_values) - len(compare_values)
                    if ld < 0:
                        other_values = tuple(chain(other_values, [0] * (-ld)))
                    elif ld > 0:
                        compare_values = tuple(chain(compare_values, [0] * ld))
                    if not compare_function(other_values, compare_values):
                        return False
        else:
            for compare_property, compare_function in compare_properties_functions:
                compare_value = getattr(self, compare_property)
                if (compare_value is not None) and not compare_function(other, compare_value):
                    return False
        return True

    def __repr__(self):
        properties_values = []
        for p in dir(self):
            if p[0] != '_':
                v = getattr(self, p)
                if not isinstance(v, Callable):
                    properties_values.append((p, v))
        return ('\n'.join(
            ['Version('] +
            [
                '    %s=%s,' % (p, repr(v))
                for p, v in properties_values
            ] +
            [')']
        ))

    def __copy__(self):
        new_instance = self.__class__()
        for a in dir(self):
            if a[0] != '_':
                v = getattr(self, a)
                if not isinstance(v, collections.Callable):
                    setattr(new_instance, a, v)
        return new_instance

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Memo
        new_instance = self.__class__()
        for a in dir(self):
            if a[0] != '_':
                v = getattr(self, a)
                if not isinstance(v, collections.Callable):
                    setattr(new_instance, a, deepcopy(v, memo=memo))
        return new_instance


# noinspection PyProtectedMember
class Meta(object):

    def __init__(
        self,
        data=None,  # type: Optional[Object]
        properties=(
            UNDEFINED
        ),  # Optional[Union[typing.Dict[str, properties.Property], Sequence[Tuple[str, properties.Property]]]]
        url=UNDEFINED,  # type: Optional[str]
    ):
        self.data = data
        self._properties = None  # type: Optional[Properties]
        if properties is not UNDEFINED:
            self.properties = properties
        self.url = None if url is UNDEFINED else url

    # noinspection PyProtectedMember
    @property
    def properties(self):
        if isinstance(self.data, type):
            property_definitions = self._properties
        else:
            if self._properties is None:
                # noinspection PyProtectedMember
                property_definitions = deepcopy(
                    get(type(self.data))._properties
                )
            else:
                property_definitions = self._properties
        if property_definitions is None:
            property_definitions = Properties()
        return property_definitions

    @properties.setter
    def properties(
        self,
        property_definitions
        # type: Optional[Union[typing.Dict[str, properties.Property], Sequence[Tuple[str, properties.Property]]]]
    ):
        if isinstance(property_definitions, Properties):
            property_definitions.meta = self
        else:
            property_definitions = Properties(property_definitions, meta=self)
        self._properties = property_definitions

    def __copy__(self):
        new_instance = self.__class__()
        for a in dir(self):
            if a[0] != '_':
                v = getattr(self, a)
                if not isinstance(v, collections.Callable):
                    setattr(new_instance, a, v)
        return new_instance

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Memo
        new_instance = self.__class__()
        for a in dir(self):
            if a != 'data' and a[0] != '_':
                v = getattr(self, a)
                if a != 'data':
                    v = deepcopy(v, memo=memo)
                if not isinstance(v, collections.Callable):
                    setattr(new_instance, a, v)
        return new_instance


class Properties(collections.OrderedDict):

    def __init__(
        self,
        items=(
            None
        ),  # type: Optional[Union[typing.Dict[str, properties.Property], Sequence[Tuple[str, properties.Property]]]]
        meta=None  # type: Optional[Meta]Optional[
    ):
        self.meta = meta
        if items is None:
            super().__init__()
        else:
            if isinstance(items, dict):
                if isinstance(items, collections.Reversible):
                    items = sorted(
                        ((k, v) for k, v in items.items())
                    )
                else:
                    items = items.items()
            super().__init__(items)

    def __copy__(self):
        # type: () -> Properties
        return self.__class__(tuple(self.items()), meta=self.meta)

    def __deepcopy__(self, memo=None):
        # type: (dict) -> Properties
        return self.__class__(
            tuple(
                (k, deepcopy(v, memo=memo))
                for k, v in self.items()
            ),
            meta=self.meta
        )


# noinspection PyProtectedMember
def get(
    o  # type: Union[type, model.Object]
):
    # type: (...) -> Union[Meta, typing.Mapping, str]
    if isinstance(o, type):
        # noinspection PyProtectedMember
        if o._meta is None:
            o._meta = Meta(data=o)
        return o._meta
    else:
        if o._meta is None:
            o._meta = deepcopy(get(type(o)))
    return o._meta


def version(data, specification, version_number):
    # type: (Any, str, Union[str, int, typing.Sequence[int]]) -> Any
    """
    Recursively alters instances of ``serial.model.Object`` according to version_number metadata associated with that
    object's properties.

    Arguments:

        - data

        - specification (str): The specification to which the ``version_number`` argument applies.

        - version_number (str|int|[int]): A version number represented as text (in the form of integers separated by
          periods), an integer, or a sequence of integers.
    """
    if isinstance(data, model.Object):
        m = get(data)
        for n, p in tuple(m.properties.items()):
            if p.versions is not None:
                version_match = False
                specification_match = False
                for v in p.versions:
                    if v.specification == specification:
                        specification_match = True
                        if v == version_number:
                            version_match = True
                            if v.types is not None:
                                m.properties[n].types = v.types
                            break
                if specification_match and (not version_match):
                    del m.properties[n]
        for n, p in m.properties.items():
            version(getattr(data, n), specification, version_number)
    elif isinstance(data, (collections.Set, collections.Sequence)) and not isinstance(data, (str, bytes)):
        for d in data:
            version(d, specification, version_number)
    elif isinstance(data, dict):
        for k, v in data.items():
            version(v, specification, version_number)
