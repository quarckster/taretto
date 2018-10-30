from functools import total_ordering

from cached_property import cached_property
from six import string_types

from taretto.ui.utils import VersionPick
from taretto.ui.core import Widget


@total_ordering
class Version(object):
    """Version class based on distutil.version.LooseVersion"""
    SUFFIXES = ('nightly', 'pre', 'alpha', 'beta', 'rc')
    SUFFIXES_STR = "|".join(r'-{}(?:\d+(?:\.\d+)?)?'.format(suff) for suff in SUFFIXES)
    component_re = re.compile(r'(?:\s*(\d+|[a-z]+|\.|(?:{})+$))'.format(SUFFIXES_STR))
    suffix_item_re = re.compile(r'^([^0-9]+)(\d+(?:\.\d+)?)?$')

    def __init__(self, vstring):
        self.parse(vstring)

    def __hash__(self):
        return hash(self.vstring)

    def parse(self, vstring):
        if vstring is None:
            raise ValueError('Version string cannot be None')
        elif isinstance(vstring, (list, tuple)):
            vstring = ".".join(map(str, vstring))
        elif vstring:
            vstring = str(vstring).strip()

        components = list(filter(lambda x: x and x != '.',
                            self.component_re.findall(vstring)))
        # Check if we have a version suffix which denotes pre-release
        if components and components[-1].startswith('-'):
            self.suffix = components[-1][1:].split('-')
            components = components[:-1]
        else:
            self.suffix = None
        for i in range(len(components)):
            try:
                components[i] = int(components[i])
            except ValueError:
                pass

        self.vstring = vstring
        self.version = components

    @cached_property
    def normalized_suffix(self):
        """Turns the string suffixes to numbers. Creates a list of tuples.

        The list of tuples is consisting of 2-tuples, the first value says the position of the
        suffix in the list and the second number the numeric value of an eventual numeric suffix.

        If the numeric suffix is not present in a field, then the value is 0
        """
        numberized = []
        if self.suffix is None:
            return numberized
        for item in self.suffix:
            suff_t, suff_ver = self.suffix_item_re.match(item).groups()
            if suff_ver is None or len(suff_ver) == 0:
                suff_ver = 0.0
            else:
                suff_ver = float(suff_ver)
            suff_t = self.SUFFIXES.index(suff_t)
            numberized.append((suff_t, suff_ver))
        return numberized

    @classmethod
    def latest(cls):
        try:
            return cls._latest
        except AttributeError:
            cls._latest = cls('latest')
            return cls._latest

    @classmethod
    def lowest(cls):
        try:
            return cls._lowest
        except AttributeError:
            cls._lowest = cls('lowest')
            return cls._lowest

    def __str__(self):
        return self.vstring

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, repr(self.vstring))

    def __lt__(self, other):
        try:
            if not isinstance(other, type(self)):
                other = Version(other)
        except Exception:
            raise ValueError('Cannot compare Version to {}'.format(type(other).__name__))

        if self == other:
            return False
        elif self == self.latest() or other == self.lowest():
            return False
        elif self == self.lowest() or other == self.latest():
            return True
        else:
            if self.version != other.version:
                return self.version < other.version
            # Use suffixes to decide
            if self.suffix is None and other.suffix is None:
                # No suffix, the same
                return False
            elif self.suffix is None:
                # This does not have suffix but the other does so this is "newer"
                return False
            elif other.suffix is None:
                # This one does have suffix and the other does not so this one is older
                return True
            else:
                # Both have suffixes, so do some math
                return self.normalized_suffix < other.normalized_suffix

    def __eq__(self, other):
        try:
            if not isinstance(other, type(self)):
                other = Version(other)
            return (
                self.version == other.version and self.normalized_suffix == other.normalized_suffix)
        except Exception:
            return False

    def __contains__(self, ver):
        """Enables to use ``in`` expression for :py:meth:`Version.is_in_series`.

        Example:
            ``"5.5.5.2" in Version("5.5") returns ``True``

        Args:
            ver: Version that should be checked if it is in series of this version. If
                :py:class:`str` provided, it will be converted to :py:class:`Version`.
        """
        try:
            return Version(ver).is_in_series(self)
        except Exception:
            return False

    def is_in_series(self, series):
        """This method checks whether the version belongs to another version's series.

        Eg.: ``Version("5.5.5.2").is_in_series("5.5")`` returns ``True``

        Args:
            series: Another :py:class:`Version` to check against. If string provided, will be
                converted to :py:class:`Version`
        """

        if not isinstance(series, Version):
            series = get_version(series)
        if self in {self.lowest(), self.latest()}:
            if series == self:
                return True
            else:
                return False
        return series.version == self.version[:len(series.version)]

    def product_version(self):
        for v, spt in version_stream_product_mapping.items():
            if self.is_in_series(v):
                return spt.product_version


def get_version(obj):
    """Return a Version based on obj."""
    if isinstance(obj, Version):
        return obj
    if not isinstance(obj, str):
        obj = str(obj)
    return Version(obj)


class VersionPicker(VersionPick):
    """An adopted version of :py:class:`widgetastic.utils.VersionPick` descriptor.

    Usage:

    """

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        # in order to keep widgetastic.utils.VersionPick behaviour
        elif isinstance(obj, Widget):
            return super(VersionPicker, self).__get__(obj)
        else:
            return self.pick(obj.application.version)

    def pick(self, active_version):
        """
        Collapses an ambiguous series of objects bound to specific versions
        by interrogating the CFME Version and returning the correct item.

        Args:
            active_version: a :py:class:`Version` instance.

        Returns:
            A value from the version dictionary.
        """
        # convert keys to Versions
        v_dict = {get_version(k): v for (k, v) in self.version_dict.items()}
        versions = v_dict.keys()
        sorted_matching_versions = sorted((v for v in versions if v <= active_version),
                                          reverse=True)
        return v_dict.get(sorted_matching_versions[0]) if sorted_matching_versions else None
