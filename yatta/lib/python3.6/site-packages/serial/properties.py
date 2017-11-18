import typing
from base64 import b64decode, b64encode
from collections import Mapping, Sequence, Set, Iterable, Callable
from copy import copy
from numbers import Real

from serial import meta, model

NoneType = type(None)


class Null(object):

    def __bool__(self):
        return False

    def __eq__(self, other):
        return True if (other is None) or isinstance(other, self.__class__) else False

    def __hash__(self):
        return 0

    def __str__(self):
        return 'null'


NULL = Null()


class Property(object):
    """
    This is the base class for defining a property.

    Properties

        - value_types ([type|Property]): One or more expected value_types or `Property` instances. Values are checked,
          sequentially, against each type or ``Property`` instance, and the first appropriate match is used.

        - required (bool): If ``True``—dumping the object will throw an error if this value is ``None``.

        - versions ([str]|{str:Property}): The property should be one of the following:

            - A set/tuple/list of version numbers to which this property applies.
            - A mapping of version numbers to an instance of `Property` applicable to that version.

          Version numbers prefixed by "<" indicate any version less than the one specified, so "<3.0" indicates that
          this property is available in versions prior to 3.0. The inverse is true for version numbers prefixed by ">".
          ">=" and "<=" have similar meanings, but are inclusive.

          Versioning can be applied to an object by calling ``serial.model.set_version`` in the ``__init__`` method of
          an ``serial.model.Object`` sub-class. For an example, see ``serial.model.OpenAPI.__init__``.

        - name (str): The name of the property when loaded from or dumped into a JSON/YAML/XML object. Specifying a
          ``name`` facilitates mapping of PEP8 compliant property to JSON or YAML attribute names, or XML element names,
          which are either camelCased, are python keywords, or otherwise not appropriate for usage in python code.

    (XML Only)

        - attribute (bool): Should this property be interpreted as an attribute (as opposed to a child element) when
          dumped as XML.

        - prefix (str): The XML prefix.

        - name_space (str): The URI of an XML name space.

    """

    json = meta.JSON(
        types=('array', 'object', 'integer', 'number', 'string', 'boolean'),
        formats=None
    )
    xml = meta.XML()

    def __init__(
        self,
        types=None,  # type: typing.Sequence[Union[type, Property]]
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[Sequence[Union[str, Version]]]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        if isinstance(types, (type, Property)):
            types = (types,)
        else:
            types = copy(types)
        self.types = types  # type: Optional[Sequence[type]]
        self.name = name
        self.required = required
        self._versions = None  # type: Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]
        self.versions = versions  # type: Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]
        self.name_space = name_space  # type: Optional[str]
        self.prefix = prefix  # type: Optional[str]
        self.attribute = attribute  # type: Optional[str]

    @property
    def versions(self):
        # type: () -> Optional[Sequence[Version]]
        return self._versions

    @versions.setter
    def versions(
        self,
        versions  # type: Optional[Sequence[Union[str, Version]]]
    ):
        # type: (...) -> Optional[Union[Mapping[str, Optional[Property]], Set[Union[str, Number]]]]
        if versions is not None:
            if isinstance(versions, (str, Number, meta.Version)):
                versions = (versions,)
            if isinstance(versions, Iterable):
                versions = tuple(
                    (v if isinstance(v, meta.Version) else meta.Version(v))
                    for v in versions
                )
            else:
                raise TypeError(
                    '``Property.versions`` requires a sequence of version strings or ' +
                    '``serial.properties.metadata.Version`` instances, not ' +
                    '``%s``.' % type(versions).__name__
                )
        self._versions = versions

    def load(self, data):
        # type: (typing.Any) -> typing.Any
        return data if self.types is None else polymorph(data, self.types)

    def dump(self, data):
        # type: (typing.Any) -> typing.Any
        return model.marshal(data)


class String(Property):
    """
    See ``serial.model.Property`` for details.

    Properties:

        - name (str)
        - required (bool)
        - versions ([str]|{str:Property})
    """

    json = meta.JSON(
        types=('string',),
        formats=(None,)
    )
    xml = meta.XML()

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        super().__init__(
            types=(str,),
            name=name,
            required=required,
            versions=versions,
            attribute=attribute,
            name_space=name_space,
            prefix=prefix,
        )


class Bytes(Property):
    """
    See ``serial.model.Property`` for details.

    Properties:

        - name (str)
        - required (bool)
        - versions ([str]|{str:Property})
    """
    json = meta.JSON(
        types=('string',),
        formats=('byte',)
    )
    xml = meta.XML()

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        super().__init__(
            types=(bytes, bytearray),
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=attribute
        )

    def load(self, data):
        # type: (str) -> bytes
        return b64decode(data)

    def dump(self, data):
        # type: (bytes) -> str
        return b64encode(data)


class Enum(Property):
    """
    See ``serial.model.Property`` for additional details.

    Properties:

        - value_types ([type|Property])

        - values ([Any]):  A list of possible values. If ``value_types`` are specified—typing is applied prior to
          validation.

        - name (str)

        - required (bool)

        - versions ([str]|{str:Property})
    """
    json = meta.JSON()
    xml = meta.XML()

    def __init__(
        self,
        types=None,  # type: Optional[Sequence[Union[type, Property]]]
        values=None,  # type: Optional[Union[typing.Sequence, typing.Set]]
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        super().__init__(
            types=types,
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=attribute
        )
        self._values = None
        self.values = values  # type: Optional[typing.Sequence]

    @property
    def values(self):
        # type: () -> Optional[Tuple]
        return self._values

    @values.setter
    def values(self, values):
        # type: (Iterable) -> None
        if (values is not None) and (not isinstance(values, (Sequence, Set))):
            raise TypeError(
                '`values` must be a finite set or sequence, not `%s`.' %
                type(values).__name__
            )
        if values is not None:
            tuple(polymorph(v, self.types) for v in values)
        self._values = values

    def load(self, data):
        # type: (typing.Any) -> typing.Any
        if self.types is not None:
            data = polymorph(data, self.types)
        if (self.values is not None) and (data not in self.values):
            raise ValueError(
                'The value provided is not a valid option:\n%s\n\n' % repr(data) +
                'Valid options include:\n%s' % (
                    ','.join(repr(t) for t in self.value_types)
                )
            )
        return data


class Number(Property):
    """
    See ``serial.model.Property`` for details.

    Properties:

        - name (str)
        - required (bool)
        - versions ([str]|{str:Property})
    """
    json = meta.JSON(
        types=('number',),
        formats=None
    )
    xml = meta.XML()

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        # type: (...) -> None
        super().__init__(
            types=(Real,),
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=attribute
        )


class Integer(Property):
    """
    See ``serial.model.Property`` for details.

    Properties:

        - name (str)
        - required (bool)
        - versions ([str]|{str:Property})
    """
    json = meta.JSON(
        types=('integer',),
        formats=None
    )
    xml = meta.XML()

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        super().__init__(
            types=(int,),
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=attribute
        )

    def load(self, data):
        # type: (typing.Any) -> typing.Any
        if (data is None) and (not self.required):
            return data
        else:
            return int(data)

    def dump(self, data):
        # type: (typing.Any) -> typing.Any
        if (data is None) and (not self.required):
            return data
        else:
            return int(data)


class Boolean(Property):
    """
    See ``serial.model.Property`` for details.

    Properties:

        - name (str)
        - required (bool)
        - versions ([str]|{str:Property})
    """
    json = meta.JSON(
        types=('boolean',),
        formats=None
    )
    xml = meta.XML()

    def __init__(
        self,
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
        attribute=False,  # type: bool
    ):
        # type: (...) -> None
        super().__init__(
            types=(bool,),
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=attribute
        )

    def load(self, data):
        # type: (typing.Any) -> typing.Any
        return bool(data)

    def dump(self, data):
        # type: (typing.Any) -> typing.Any
        return bool(data)


class Array(Property):
    """
    See ``serial.model.Property`` for details.

    Properties:

        - item_types (type|Property|[type|Property]): The type(s) of values/objects contained in the array. Similar to
          ``serial.model.Property().value_types``, but applied to items in the array, not the array itself.

        - name (str)

        - required (bool)

        - versions ([str]|{str:Property})
    """
    json = meta.JSON(
        types=('array',),
        formats=None
    )
    xml = meta.XML()

    def __init__(
        self,
        item_types=None,  # type: Optional[Union[type, typing.Sequence[Union[type, Property]]]]
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[typing.Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
    ):
        super().__init__(
            types=(model.Array,),
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=False
        )
        if isinstance(item_types, (type, Property)):
            item_types = (item_types,)
        self.item_types = item_types  # type: Optional[typing.Sequence[Union[type, Property]]]

    def load(self, data):
        # type: (typing.Any) -> typing.Any
        return (
            data if data is None
            else model.Array(
                data,
                item_types=self.item_types
                # [polymorph(d, self.item_types) for d in data]
            )
        )


def validate(data, types):
    # type: (Union[model.Object, model.Array], Seqeunce[Union[type, Property]]) -> None
    # TODO: serial.properties.validate
    if types is not None:
        pass


def polymorph(data, types):
    # type: (Any, typing.Sequence[Union[type, Property]]) -> typing.Any
    if data is None:
        return data
    elif types is None:
        if isinstance(data, dict) and not isinstance(data, model.Dictionary):
            data = model.Dictionary(data)
        elif isinstance(data, (Set, Sequence)) and (not isinstance(data, (str, bytes, model.Array))):
            data = model.Array(data)
        return data
    if isinstance(types, Callable):
        types = types(data)
    closest_match = None
    data_keys = None
    matched = False
    for t in types:
        if isinstance(
            t,
            Property
        ):
            if closest_match is None:
                try:
                    data = t.load(data)
                    matched = True
                    break
                except TypeError:
                    continue
        elif isinstance(t, type):
            if (
                issubclass(t, model.Object) and
                isinstance(data, Mapping)
            ):
                data_keys = data_keys or set(data.keys())
                property_definitions = meta.get(t).properties
                type_keys = {
                    (v.name or k)
                    for k, v in property_definitions.items()
                }
                if not (data_keys - type_keys):
                    unused = type_keys - data_keys
                    if (
                        (closest_match is None) or
                        len(unused) < len(closest_match[-1])
                    ):
                        closest_match = (t, unused)
            elif isinstance(data, dict) and issubclass(t, (model.Dictionary, dict)):
                data = model.Dictionary(data)
                matched = True
                break
            elif (
                isinstance(data, (Set, Sequence)) and
                (not isinstance(data, (str, bytes))) and
                issubclass(t, (Set, Sequence)) and
                (not issubclass(t, (str, bytes, model.Array)))
            ):
                data = model.Array(data)
                matched = True
                break
            elif isinstance(data, t):
                matched = True
                break
    if closest_match is not None:
        data = closest_match[0](data)
    elif not matched:
        raise TypeError(
            'The data provided does not fit any of the types indicated.\n\n' +
            ' - data: %s\n\n' % model.serialize(data) +
            ' - types: %s' % repr(types)
        )
    return data


class Object(Property):
    """
    See ``serial.model.Property`` for details.

    Properties:

        - value_types (type|Property|[type|Property]): The type(s) of values/objects comprising the mapped
          values. Similar to ``serial.model.Property().value_types``, but applies to *values* in the dictionary object,
          not the object itself.

        - name (str)

        - required (bool)

        - versions ([str]|{str:Property})
    """
    json = meta.JSON(
        types=('object',),
        formats=None
    )
    xml = meta.XML()

    def __init__(
        self,
        types=None,  # type: Optional[Union[type, Sequence[Union[type, Property]]]]
        value_types=None,  # type: Optional[Union[type, Sequence[Union[type, Property]]]]
        name=None,  # type: Optional[str]
        required=False,  # type: bool
        versions=None,  # type: Optional[Collection]
        name_space=None,  # type: Optional[str]
        prefix=None,  # type: Optional[str]
    ):
        # type: (...) -> None
        if types is None:
            types = (model.Dictionary,)
        super().__init__(
            types=types,
            name=name,
            required=required,
            versions=versions,
            name_space=name_space,
            prefix=prefix,
            attribute=False
        )
        if value_types is not None:
            if isinstance(value_types, (type, Property)):
                value_types = (value_types,)
        self.value_types = value_types
