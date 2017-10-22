
import collections
import json
import typing
from base64 import b64encode
from copy import deepcopy
from http.client import HTTPResponse
from io import IOBase, UnsupportedOperation
from itertools import chain
from numbers import Number
from typing import Union, Any, AnyStr

import yaml

from serial import properties, meta
from serial.errors import ValidationError


def marshal(data):
    # type: (Any) -> Union[Object, str, Number, bytes, typing.Collection]
    """
    Recursively converts instances of ``serial.model.Object`` into JSON/YAML serializable objects.
    """
    if hasattr(data, '_marshal'):
        return data._marshal()
    elif isinstance(data, properties.Null):
        return None
    elif isinstance(data, (bytes, bytearray)):
        return b64encode(data)
    elif hasattr(data, '__bytes__'):
        return b64encode(bytes(data))
    else:
        return data


def serialize(data, data_format='json'):
    # type: (Any, str) -> str
    """
    Serializes instances of ``serial.model.Object`` as JSON or YAML.
    """
    if data_format not in ('json', 'yaml'):
        data_format = data_format.lower()
        if data_format not in ('json', 'yaml'):
            raise ValueError(
                'Supported `serial.model.serialize()` `data_format` values include "json" and "yaml" (not "%s").' % data_format
            )
    if data_format == 'json':
        return json.dumps(marshal(data))
    elif data_format == 'yaml':
        return yaml.dump(marshal(data))


def deserialize(data):
    if isinstance(data, IOBase):
        try:
            data.seek(0)
        except UnsupportedOperation:
            pass
        if hasattr(data, 'readall'):
            data = data.readall()
        else:
            data = data.read()
    if isinstance(data, bytes):
        data = str(data, encoding='utf-8')
    if isinstance(data, str):
        try:
            data = json.loads(data, object_hook=collections.OrderedDict)
        except json.JSONDecodeError as e:
            data = yaml.load(data)
    return data


class Object(object):

    _meta = None  # type: Optional[meta.Meta]

    def __init__(
        self,
        _=None,  # type: Optional[Union[AnyStr, typing.Mapping, typing.Sequence, typing.IO]]
    ):
        self._meta = None
        if _ is not None:
            if isinstance(_, HTTPResponse):
                meta.get(self).url = _.url
            _ = deserialize(_)
            for k, v in _.items():
                try:
                    self[k] = v
                except KeyError as e:
                    if e.args and len(e.args) == 1:
                        e.args = (
                            r'%s.%s: %s' % (type(self).__name__, e.args[0], json.dumps(_)),
                        )
                    raise e

    def __setattr__(self, property_name, value):
        # type: (Object, str, Any) -> properties_.NoneType
        if property_name[0] != '_':
            property_definition = meta.get(self).properties[property_name]
            try:
                value = property_definition.load(value)
            except TypeError as e:
                message = '%s.%s: ' % (
                    self.__class__.__name__,
                    property_name
                )
                if e.args:
                    e.args = tuple(
                        chain(
                            (message + e.args[0],),
                            e.args[1:]
                        )
                    )
                else:
                    e.args = (message + repr(value),)
                raise e
        super().__setattr__(property_name, value)

    def __setitem__(self, key, value):
        # type: (str, str) -> None
        try:
            property_definition = meta.get(self).properties[key]
            property_name = key
        except KeyError:
            property_definition = None
            property_name = None
            for pn, pd in meta.get(self).properties.items():
                if key == pd.name:
                    property_name = pn
                    property_definition = pd
                    break
            if property_name is None:
                raise KeyError(
                    '`%s` has no property mapped to the name "%s"' % (
                        self.__class__.__name__,
                        key
                    )
                )
        if (
            (value is None) and
            property_definition.required and
            (
                properties.NoneType not in (
                    property_definition.types(value)
                    if isinstance(property_definition.types, collections.Callable)
                    else property_definition.types
                )
            )
        ):
            raise ValidationError(
                'The property `%s` is required for `serial.model.%s.%s`.' % (
                    property_name,
                    self.__class__.__name__
                )
            )
        try:
            setattr(self, property_name, value)
        except TypeError as e:
            e.args = tuple(chain(
                (
                    '`%s.%s`: %s' % (
                        self.__class__.__name__,
                        property_name,
                        e.args[0] if e else ''
                    ),
                ),
                e.args[1:] if e.args else tuple()
            ))
            raise e
        return None

    def __getitem__(self, key):
        # type: (str, str) -> None
        try:
            property_definition = meta.get(self).properties[key]
            property_name = key
        except KeyError as e:
            property_definition = None
            property_name = None
            for pn, pd in meta.get(self).properties.items():
                if key == pd.name:
                    property_name = pn
                    property_definition = pd
                    break
            if property_definition is None:
                raise KeyError(
                    '`%s` has no property mapped to the name "%s"' % (
                        self.__class__.__name__,
                        key
                    )
                )
        return getattr(self, property_name)

    def __copy__(self):
        # type: () -> Object
        m = meta.get(self)
        new_instance = self.__class__()
        new_instance._meta = deepcopy(m)
        new_instance._meta.data = new_instance
        for k in m.properties.keys():
            try:
                setattr(new_instance, k, getattr(self, k))
            except TypeError as e:
                label = '%s.%s: ' % (self.__class__.__name__, k)
                if e.args:
                    e.args = tuple(
                        chain(
                            (label + e.args[0],),
                            e.args[1:]
                        )
                    )
                else:
                    e.args = (label + serialize(self),)
                raise e
        return new_instance

    def __deepcopy__(self, memo=None):
        # type: (Optional[dict]) -> Object
        m = meta.get(self)
        new_instance = self.__class__()
        new_instance._meta = deepcopy(m)  # type: meta.Meta
        new_instance._meta.data = new_instance  # type: Object
        for k in m.properties.keys():
            try:
                setattr(new_instance, k, deepcopy(getattr(self, k), memo=memo))
            except TypeError as e:
                label = '%s.%s: ' % (self.__class__.__name__, k)
                if e.args:
                    e.args = tuple(
                        chain(
                            (label + e.args[0],),
                            e.args[1:]
                        )
                    )
                else:
                    e.args = (label + serialize(self),)
                raise e
        return new_instance

    def _marshal(self):
        data = collections.OrderedDict()
        for pn, p in meta.get(self).properties.items():
            v = getattr(self, pn)
            if v is None:
                if p.required:
                    raise ValidationError(
                        'The property `%s` is required for `serial.model.%s`.' % (pn, self.__class__.__name__)
                    )
            else:
                v = marshal(v)
                k = p.name or pn
                if (v is None) and (p.types is not None) and (properties.Null not in p.types):
                    raise TypeError(
                        'Null values are not allowed in `serial.model.%s.%s`.' % (self.__class__.__name__, pn)
                    )
                data[k] = v
        return data

    def __str__(self):
        return json.dumps(marshal(self))

    def __eq__(self, other):
        # type: (Any) -> bool
        if isinstance(other, self.__class__):
            m = meta.get(self)
            other_meta = meta.get(other)
            self_properties = set(m.properties.keys())
            other_properties = set(other_meta.properties.keys())
            if self_properties != other_properties:
                return False
            for p in self_properties|other_properties:
                sp = getattr(self, p)
                op = getattr(other, p)
                if sp != op:
                    # print('%s(%s)\n!=\n%s(%s)\n\n' % (type(sp).__name__, serialize(sp), type(op).__name__, serialize(op)))
                    return False
            return True
        else:
            return False

    def __ne__(self, other):
        # type: (Any) -> bool
        return False if self == other else True

    def __iter__(self):
        for k in meta.get(self).properties.keys():
            yield k


class Array(list):

    def __init__(
        self,
        items=None,  # type: Optional[Union[Sequence, Set]]
        item_types=None,  # type: Optional[Union[Sequence[Union[type, properties_.Property]], type, properties_.Property]]
    ):
        if isinstance(items, (str, bytes)):
            raise TypeError(
                'Array items must be a set or sequence, not `%s`:\n%s' % (
                    type(items).__name__,
                    repr(items)
                )
            )
        if isinstance(item_types, (type, properties.Property)):
            item_types = (item_types,)
        self.item_types = item_types
        for item in items:
            self.append(item)
        if items:
            super().__init__(
                properties.polymorph(item, self.item_types)
                for item in items
            )

    def __setitem__(
        self,
        index,  # type: int
        value,  # type: Any
    ):
        super().__setitem__(index, properties.polymorph(value, self.item_types))

    def append(self, value):
        # type: (Any) -> None
        super().append(properties.polymorph(value, self.item_types))

    def __copy__(self):
        # type: (Array) -> Array
        return self.__class__(tuple(self[:]), item_types=self.item_types)

    def __deepcopy__(self, memo):
        # type: (dict) -> Array
        return self.__class__(tuple(deepcopy(i, memo) for i in self[:]), item_types=self.item_types)

    def _marshal(self):
        return tuple(
            marshal(i) for i in self
        )


class Dictionary(collections.OrderedDict):

    def __init__(
        self,
        items=None,  # type: Optional[typing.Mapping]
        value_types=None,  # type: Optional[Union[Sequence[Union[type, properties_.Property]], type, properties_.Property]]
    ):
        if isinstance(value_types, (type, properties.Property)):
            value_types = (value_types,)
        self.value_types = value_types
        if items is not None:
            if items is None:
                super().__init__()
            else:
                super().__init__(items)

    def __setitem__(
        self,
        key,  # type: int
        value,  # type: Any
    ):
        super().__setitem__(key, properties.polymorph(value, self.value_types))

    def __copy__(self):
        # type: (Dictionary) -> Dictionary
        return self.__class__(self.items(), value_types=self.value_types)

    def __deepcopy__(self, memo):
        # type: (dict) -> Dictionary
        return self.__class__(
            [
                (k, deepcopy(v, memo)) for k, v in self.items()
            ],
            value_types=self.value_types
        )

    def _marshal(self):
        return collections.OrderedDict(
            [
                (k, marshal(v)) for k, v in self.items()
            ]
        )
