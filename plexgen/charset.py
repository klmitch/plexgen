# Copyright (C) 2016 by Kevin L. Mitchell <klmitch@mit.edu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see
# <http://www.gnu.org/licenses/>.

import abc
import collections

import six

from plexgen import prioq


# Character range constants
MIN_CHAR = 0
MAX_CHAR = 0x10ffff
FULL_LENGTH = MAX_CHAR - MIN_CHAR + 1

# Constants for _qchar()
MIN_GRAPH = ord(u' ')  # minimum ASCII graph characters
MAX_GRAPH = ord(u'~')  # maximum ASCII graph characters
ESCAPED = set(ord(c) for c in u'[]\\-^')  # chars to escape
SUBSTITUTE = {  # Substitutions
    0: u'\\0',
    7: u'\\a',
    8: u'\\b',
    9: u'\\t',
    10: u'\\n',
    11: u'\\v',
    12: u'\\f',
    13: u'\\r',
    27: u'\\e',
}


# Representation of a character range
Range = collections.namedtuple('Range', ['start', 'end'])


def _vchars(*chars):
    """
    Validate characters are within the proper range.

    :param *chars: The characters, expressed as integers, to validate.

    :raises ValueError:
        One of the input integers was outside the valid range.
    """

    for c in chars:
        if c < MIN_CHAR or c > MAX_CHAR:
            raise ValueError('invalid character code %s' % c)


def _qchar(char):
    """
    Quotes a character for display.

    :param int char: The character to quote, expressed as a code
                     point.

    :returns: The display string for the character.
    :rtype: ``str``
    """

    # If it's in the graphical range, use it directly (possibly with
    # escaping)
    if MIN_GRAPH <= char <= MAX_GRAPH:
        if char in ESCAPED:
            return u'\\%s' % six.unichr(char)
        return six.unichr(char)

    # If it has a substitution, use that
    elif char in SUBSTITUTE:
        return SUBSTITUTE[char]

    # Convert to an escape sequence
    elif char <= 0xff:
        return u'\\x%02x' % char
    elif char <= 0xffff:
        return u'\\u%04x' % char
    return u'\\U%08x' % char


def _rngstr(rng):
    """
    Produce a proper representation of a range.

    :param rng: The range to produce a representation of.
    :type rng: ``Range``

    :returns: The proper string representation of the range.
    :rtype: ``str``
    """

    if rng.start == rng.end:
        # Single-character range
        return _qchar(rng.start)
    elif rng.start == rng.end - 1:
        # Two-character range
        return u'%s%s' % (_qchar(rng.start), _qchar(rng.end))

    # Longer range
    return u'%s-%s' % (_qchar(rng.start), _qchar(rng.end))


def _search_ranges(ranges, item, lo=0, hi=None):
    """
    Search the ``ranges`` list for the given item.  This is
    implemented using a binary search.

    :param list ranges: A sorted list of ``Range`` instances to
                        search.
    :param int item: The code point of the item to locate.
    :param int lo: The starting point of the interval to search.
                   Default is 0.
    :param int hi: The ending point of the interval to search.
                   Default is the length of the ranges.

    :returns: A 2-tuple, where the first element specifies the index
              of a range containing ``item`` or a location in the
              ``ranges`` list where one could be inserted; the second
              element is a boolean indicating whether the item was
              found.
    """

    # Note: Adapted from standard Python "bisect" library, but
    # with additions due to the fact that we're storing ranges of
    # items, not the items themselves.

    # Sanity-check and normalize the bisection variables
    if hi is None:
        hi = len(ranges)
    if lo < 0 or lo > min(hi, len(ranges)):
        raise IndexError('lo out of range')
    if hi > len(ranges):
        raise IndexError('hi out of range')

    # If there are no ranges, we have our answer
    if not ranges[lo:hi]:
        return lo, False

    while lo < hi:
        mid = (lo + hi) // 2

        if ranges[mid].start <= item <= ranges[mid].end:
            # Item is contained in a range at the midpoint
            return mid, True

        elif item < ranges[mid].start:
            # Item is to the left
            hi = mid

        else:
            # Item is to the right
            lo = mid + 1

    # Never hit a range containing the item, so return insertion
    # point
    return lo, False


def _add_range(ranges, start, end, start_hint=None, end_hint=None):
    """
    Add a range to a ``ranges`` list.

    :param list ranges: The list of ranges.  This list will be
                        modified in place.
    :param int start: The starting point of the range to add.
    :param int end: The ending point of the range to add.
    :param tuple start_hint: A tuple of an index and a "contained"
                             flag for the starting point, as returned
                             by ``_search_ranges()``.  If not
                             provided, ``_search_ranges()`` will be
                             called.
    :param tuple end_hint: A tuple of an index and a "contained" flag
                           for the ending point, as returned by
                           ``_search_ranges()``.  If not provided,
                           ``_search_ranges()`` will be called.

    :returns: The modified ranges list, for convenience.
    :rtype: ``list``
    """

    start_idx, start_contained = (_search_ranges(ranges, start)
                                  if start_hint is None else start_hint)
    end_idx, end_contained = (_search_ranges(ranges, end, start_idx)
                              if end_hint is None else end_hint)

    # If the whole range is already contained, nothing to do
    if start_idx == end_idx and start_contained and end_contained:
        return ranges

    # Figure out the start point and end point of the new range
    if start_contained:
        start = ranges[start_idx].start
    if end_contained:
        end = ranges[end_idx].end
        end_idx += 1

    # Check for range merge
    if start_idx > 0 and ranges[start_idx - 1].end + 1 == start:
        start_idx -= 1
        start = ranges[start_idx].start
    if end_idx < len(ranges) and ranges[end_idx].start == end + 1:
        end = ranges[end_idx].end
        end_idx += 1

    # Update the ranges list
    ranges[start_idx:end_idx] = [Range(start, end)]

    return ranges


def _discard_range(ranges, start, end, start_hint=None, end_hint=None):
    """
    Remove a range from a ``ranges`` list.

    :param list ranges: The list of ranges.  This list will be
                        modified in place.
    :param int start: The starting point of the range to remove.
    :param int end: The ending point of the range to remove.
    :param tuple start_hint: A tuple of an index and a "contained"
                             flag for the starting point, as returned
                             by ``_search_ranges()``.  If not
                             provided, ``_search_ranges()`` will be
                             called.
    :param tuple end_hint: A tuple of an index and a "contained" flag
                           for the ending point, as returned by
                           ``_search_ranges()``.  If not provided,
                           ``_search_ranges()`` will be called.

    :returns: The modified ranges list, for convenience.
    :rtype: ``list``
    """

    start_idx, start_contained = (_search_ranges(ranges, start)
                                  if start_hint is None else start_hint)
    end_idx, end_contained = (_search_ranges(ranges, end, start_idx)
                              if end_hint is None else end_hint)

    # If the whole range is already excluded, nothing to do
    if start_idx == end_idx and not start_contained and not end_contained:
        return ranges

    # Compute the replacement ranges
    repl = []
    if start_contained:
        if ranges[start_idx].start != start:
            repl.append(Range(ranges[start_idx].start, start - 1))
    if end_contained:
        if ranges[end_idx].end != end:
            repl.append(Range(end + 1, ranges[end_idx].end))
        end_idx += 1

    # Update the ranges list
    ranges[start_idx:end_idx] = repl

    return ranges


def _invert(ranges):
    """
    Return an iterator of the character ranges excluded by a given
    range.

    :param list ranges: The range list to invert.

    :returns: A generator producing ``Range`` instances.
    """

    # Start off configured to exclude the whole range
    start = MIN_CHAR
    end = MAX_CHAR

    # Walk through the ranges
    for rng in ranges:
        # Update the end of the excluded range
        end = rng.start - 1
        if start <= end:
            # We have a valid range, yield it
            yield Range(start, end)

        # Reset for the next interval
        start = rng.end + 1
        end = MAX_CHAR

    if start <= end:
        # Yield the last range
        yield Range(start, end)


def _intersection(ranges1, ranges2):
    """
    Construct the intersection of two range lists.

    :param list ranges1: The first range list.
    :param list ranges2: The second range list.

    :returns: The intersection of both range lists.
    :rtype: ``list``
    """

    # Arrange for ranges1 to be the longest list
    if len(ranges1) < len(ranges2):
        ranges1, ranges2 = ranges2, ranges1

    # Copy the list (or tuple)
    ranges1 = list(ranges1)

    # Remove elements from the inverse
    for rng in _invert(ranges2):
        _discard_range(ranges1, rng.start, rng.end)

    return ranges1


def _union(ranges1, ranges2):
    """
    Construct the union of two range lists.

    :param list ranges1: The first range list.
    :param list ranges2: The second range list.

    :returns: The union of both range lists.
    :rtype: ``list``
    """

    # Arrange for ranges1 to be the longest list
    if len(ranges1) < len(ranges2):
        ranges1, ranges2 = ranges2, ranges1

    # Copy the list (or tuple)
    ranges1 = list(ranges1)

    # Add elements from the other ranges list
    for rng in ranges2:
        _add_range(ranges1, rng.start, rng.end)

    return ranges1


def _difference(ranges1, ranges2):
    """
    Construct the difference of two range lists.

    :param list ranges1: The first range list.
    :param list ranges2: The second range list.

    :returns: The result of removing all the elements of ``ranges2``
              from ``ranges1``.
    :rtype: ``list``
    """

    # Copy the list (or tuple)
    ranges1 = list(ranges1)

    # Remove elements from the other ranges list
    for rng in ranges2:
        _discard_range(ranges1, rng.start, rng.end)

    return ranges1


def _sym_difference(ranges1, ranges2):
    """
    Construct the symmetric difference of two range lists.

    :param list ranges1: The first range list.
    :param list ranges2: The second range list.

    :returns: The result of computing the symmetric difference of the
              ranges.
    :rtype: ``list``
    """

    # Compute intermediate ranges; this is equivalent to computing
    # tmp1=(ranges1 & ~ranges2) and tmp2=(ranges2 & ~ranges1), but
    # avoids a double call to _invert()
    tmp1 = list(ranges1)
    tmp2 = list(ranges2)
    for rng in ranges2:
        _discard_range(tmp1, rng.start, rng.end)
    for rng in ranges1:
        _discard_range(tmp2, rng.start, rng.end)

    # Now just need the union of those two sets of ranges
    return _union(tmp1, tmp2)


def _isdisjoint(ranges1, ranges2):
    """
    Determine if two lists of ranges are disjoint.

    :param list ranges1: The first range list.
    :param list ranges2: The second range list.

    :returns: A ``True`` value if the ranges are disjoint.
    :rtype: ``bool``
    """

    # Arrange for ranges1 to be the longest list
    if len(ranges1) < len(ranges2):
        ranges1, ranges2 = ranges2, ranges1

    # Look up each range from ranges2 and see if it's contained
    for rng in ranges2:
        start_idx, start_contained = _search_ranges(ranges1, rng.start)
        end_idx, end_contained = _search_ranges(ranges1, rng.end, start_idx)

        # If it's not wholely excluded, then the sets aren't disjoint
        if start_idx != end_idx or start_contained or end_contained:
            return False

    return True


@six.python_2_unicode_compatible
@six.add_metaclass(abc.ABCMeta)
class BaseCharSet(collections.Set):
    """
    Represent a set of characters.  This differs from the standard
    Python ``set`` type by storing compact ranges of characters.  A
    ``disjoint()`` class method allows decomposition of several
    potentially overlapping character sets into disjoint (but possibly
    adjoining) character sets.  This is an abstract base class; use
    the ``CharSet`` or ``FrozenCharSet`` classes.
    """

    @classmethod
    def disjoint(cls, *csets):
        """
        Compute the disjoint of two or more character sets.  That is,
        given two or more possibly overlapping character sets, this
        generator produces a sequence of character sets that do not
        overlap, along with a list of the input character sets that
        adjoin each of the produced character sets.  Note that the
        produced character sets cover only a single range, but the
        input character sets may be of any complexity.

        :param *csets: The input character sets, instances of
                       ``CharSet``.

        :returns: A generator that yield two-element tuples; the first
                  element will be a ``CharSet`` instance, and the
                  second element will be a list of the input
                  ``CharSet`` instances that are supersets of the
                  first element.
        """

        # This is a dense little algorithm.  It works by creating a
        # work queue using a priority queue data structure; the
        # elements in the work queue are tuples of the ranges from the
        # character sets and a list of the character sets the range is
        # found in.  The priority queue is sorted such that range
        # start points are sorted ascending, followed by sorting the
        # ranges by length, which ensures that, for any entry in the
        # queue, later entries with the same start point are either
        # duplicates or supersets.
        #
        # After popping an item off, we pop off any duplicates
        # (merging the lists of contributing character sets), then
        # temporarily save all supersets.  If we find an entry that
        # overlaps but is not a superset, then we split the working
        # range in two and produce only the first half of the range.
        # After that, the supersets are all split and added back to
        # the queue, followed by the second half of the working range
        # (if necessary).  Rinse, lather, repeat, until all the ranges
        # have been processed.
        #
        # The end result is a sequence of CharSet instances containing
        # simple ranges and a list of the input CharSet instances that
        # are supersets of the result CharSet (so callers can identify
        # containers-of-Charset that need to be split).

        # Begin by setting up the priority work queue and extracting
        # the range lists from all the input character sets
        ranges = prioq.PrioQ(key=lambda x:
                             (x[0].start, (x[0].end - x[0].start + 1)))
        for cset in csets:
            ranges.push(*((rng, [cset]) for rng in cset.ranges))

        # Begin the workq
        while ranges:
            # Pop off a range to work with
            rng, csets = ranges.pop()

            # Collapse duplicate ranges
            while ranges and ranges.top[0] == rng:
                csets.extend(ranges.top[1])
                ranges.pop()

            # Select the start and end of the range we will produce
            start = rng.start
            end = rng.end

            # Find all supersets (sorting criteria above ensures that
            # all ranges after this one that share the same starting
            # point are either identical or supersets)
            fcsets = csets[:]
            supersets = []
            while ranges:
                if ranges.top[0].start <= start:
                    # Found a superset
                    fcsets.extend(ranges.top[1])
                    supersets.append(ranges.pop())
                else:
                    # OK, not a superset; does it overlap?
                    if ranges.top[0].start <= end:
                        # Yep, clamp the end of the produced range
                        end = ranges.top[0].start - 1

                    # We're done finding supersets/overlaps
                    break

            # Produce the disjoint character set
            yield cls(start, end), fcsets

            # Move up the start endpoint for splitting the supersets
            start = end + 1

            # Split the supersets
            ranges.push(*((Range(start, suset[0].end), suset[1])
                          for suset in supersets))

            # If the working range wasn't fully consumed, split it and
            # add the unconsumed portion to the workq
            if start < rng.end:
                ranges.push((Range(start, rng.end), csets))

    @abc.abstractmethod
    def __init__(self, ranges):
        """
        Initialize a ``BaseCharSet`` instance.

        :param ranges: The list or tuple of ranges for the set.
        """

        self.ranges = ranges

        # Cache the length of the set; this must be invalidated after
        # any changes to the set
        self._len_cache = None

    def __str__(self):
        """
        Return a string representation of the character set.

        :returns: An appropriate representation of the character set.
        :rtype: ``str``
        """

        # Grab the length of the set first
        length = len(self)

        # Handle the simple cases first
        if length == 0:
            return u'[]'
        elif length == FULL_LENGTH:
            return u'[^]'
        elif length == FULL_LENGTH - 1 and u'\n' not in self:
            return u'.'

        # Should we use exclusion syntax or inclusion syntax?
        if length > FULL_LENGTH // 2:
            pfx = u'^'
            ranges = _invert(self.ranges)
        else:
            pfx = u''
            ranges = self.ranges

        return u'[%s%s]' % (pfx, u''.join(_rngstr(rng) for rng in ranges))

    def __contains__(self, item):
        """
        Determine whether a character (specified as either a string or an
        integer) exists within the set.

        :param item: The character to check.  May be either a
                     1-character string or an integer.

        :returns: A ``True`` value if the set contains the character.
        :rtype: ``bool``
        """

        # Convert string to integer
        if isinstance(item, six.string_types):
            item = ord(item)

        return _search_ranges(self.ranges, item)[1]

    def __iter__(self):
        """
        Iterate over all characters contained in the set.

        :returns: A generator that produces each character contained
                  in the set in sequence.  Characters are returned as
                  single-character strings.
        """

        for rng in self.ranges:
            for i in range(rng.start, rng.end + 1):
                yield six.unichr(i)

    def __len__(self):
        """
        Compute and return the length of the set.  The length of a
        character set is the number of characters contained in the
        set.

        :returns: Length of the set.
        :rtype: ``int``
        """

        # Only recompute if necessary
        if self._len_cache is None:
            self._len_cache = sum((rng.end - rng.start) + 1
                                  for rng in self.ranges)

        return self._len_cache

    def __eq__(self, other):
        """
        Compare two character sets for equality.  This defers to
        ``collections.Set`` if ``other`` is not a ``BaseCharSet``.

        :param other: Another object to compare to.

        :returns: A ``True`` value if the sets are equal.
        :rtype: ``bool``
        """

        if isinstance(other, BaseCharSet):
            return (len(self.ranges) == len(other.ranges) and
                    all(a == b for a, b in zip(self.ranges, other.ranges)))
        return super(BaseCharSet, self).__eq__(other)

    def __ne__(self, other):
        """
        Compare two character sets for inequality.  This defers to
        ``collections.Set`` if ``other`` is not a ``BaseCharSet``.

        :param other: Another object to compare to.

        :returns: A ``True`` value if the sets are not equal.
        :rtype: ``bool``
        """

        if isinstance(other, BaseCharSet):
            return (len(self.ranges) != len(other.ranges) or
                    any(a != b for a, b in zip(self.ranges, other.ranges)))
        return super(BaseCharSet, self).__ne__(other)

    def __le__(self, other):
        """
        Determine whether this character set is a subset of another.

        :param other: Another object to compare to.

        :returns: A ``True`` value if this character set is a subset
                  of another.
        :rtype: ``bool``
        """

        if isinstance(other, BaseCharSet):
            return self.__eq__(other) or self._issubset(other)
        return super(BaseCharSet, self).__le__(other)

    def __lt__(self, other):
        """
        Determine whether this character set is a proper subset of
        another.

        :param other: Another object to compare to.

        :returns: A ``True`` value if this character set is a proper
                  subset of another.
        :rtype: ``bool``
        """

        if isinstance(other, BaseCharSet):
            return self.__ne__(other) and self._issubset(other)
        return super(BaseCharSet, self).__lt__(other)

    def __ge__(self, other):
        """
        Determine whether another character set is a subset of this one.

        :param other: Another object to compare to.

        :returns: A ``True`` value if the other character set is a
                  subset of this one.
        :rtype: ``bool``
        """

        if isinstance(other, BaseCharSet):
            return self.__eq__(other) or other._issubset(self)

        # Copied from Python 2.7 library, because it doesn't work
        # properly in Python 3.4
        if not isinstance(other, collections.Set):
            return NotImplemented
        if len(self) < len(other):
            return False
        for elem in other:
            if elem not in self:
                return False
        return True

    def __gt__(self, other):
        """
        Determine whether another character set is a proper subset of this
        one.

        :param other: Another object to compare to.

        :returns: A ``True`` value if the other character set is a
                  proper subset of this one.
        :rtype: ``bool``
        """

        if isinstance(other, BaseCharSet):
            return self.__ne__(other) and other._issubset(self)

        # Copied from Python 2.7 library, because it doesn't work
        # properly in Python 3.4
        if not isinstance(other, collections.Set):
            return NotImplemented
        return len(self) > len(other) and self.__ge__(other)

    def __invert__(self):
        """
        Invert a character set.  This produces a new character set that
        excludes all the characters included by this character set.

        :returns: The inverted character set.
        :rtype: ``BaseCharSet``
        """

        # Construct and return a new BaseCharSet
        return self.__class__(None, _invert(self.ranges))

    def __and__(self, other):
        """
        Generate the intersection between this character set and another.

        :param other: Another object to compute an intersection with.

        :returns: A new character set containing the intersection.
        :rtype: ``BaseCharSet``
        """

        if isinstance(other, BaseCharSet):
            if self == other:
                # Short cut the identical sets case
                return self.__class__(self)
            return self.__class__(None, _intersection(self.ranges,
                                                      other.ranges))
        return super(BaseCharSet, self).__and__(other)

    def __or__(self, other):
        """
        Generate the union between this character set and another.

        :param other: Another object to compute the union with.

        :returns: A new character set containing the union.
        :rtype: ``BaseCharSet``
        """

        if isinstance(other, BaseCharSet):
            if self == other:
                # Short cut the identical sets case
                return self.__class__(self)
            return self.__class__(None, _union(self.ranges, other.ranges))
        return super(BaseCharSet, self).__or__(other)

    def __sub__(self, other):
        """
        Generate the difference between this character set and another.

        :param other: Another object to compute the difference with.

        :returns: A new character set containing the difference.
        :rtype: ``BaseCharSet``
        """

        if isinstance(other, BaseCharSet):
            if self == other:
                # Short cut the emptied set case
                return self.__class__()
            return self.__class__(None, _difference(self.ranges, other.ranges))
        return super(BaseCharSet, self).__sub__(other)

    def __xor__(self, other):
        """
        Generate the symmetric difference between this character set and
        another.

        :param other: Another object to compute the symmetric
                      difference with.

        :returns: A new character set containing the symmetric
                  difference.
        :rtype: ``BaseCharSet``
        """

        if isinstance(other, BaseCharSet):
            if self == other:
                # Short cut the emptied set case
                return self.__class__()
            return self.__class__(None, _sym_difference(self.ranges,
                                                        other.ranges))
        return super(BaseCharSet, self).__xor__(other)

    def _issubset(self, other):
        """
        Determine if this character set is a subset of another.  This is
        performed by comparing ranges, for efficiency.

        :param other: Another character set to compare to.
        :type other: ``BaseCharSet``

        :returns: A ``True`` value if this character set is a subset
                  of the other.
        :rtype: ``bool``
        """

        # Search our ranges
        idx = 0
        for rng in self.ranges:
            # Search for the starting point in the other set
            idx, contained = _search_ranges(other.ranges, rng.start, lo=idx)
            if not contained or rng.end > other.ranges[idx].end:
                # Can't be a subset, then
                return False

        return True

    def isdisjoint(self, other):
        """
        Determine if another character set is disjoint from this character
        set; that is, if they have no elements in common.

        :param other: Another character set to compare to.
        :type other: ``BaseCharSet``

        :returns: A ``True`` value if the character sets are disjoint.
        :rtype: ``bool``
        """

        if isinstance(other, BaseCharSet):
            return _isdisjoint(self.ranges, other.ranges)
        return super(BaseCharSet, self).isdisjoint(other)


class CharSet(BaseCharSet, collections.MutableSet):
    """
    Represent a set of characters.  This differs from the standard
    Python ``set`` type by storing compact ranges of characters.  A
    ``disjoint()`` class method allows decomposition of several
    potentially overlapping character sets into disjoint (but possibly
    adjoining) character sets.
    """

    def __init__(self, start=None, end=None):
        """
        Initialize a ``CharSet`` instance.

        :param start: If a string, the lower bound of a character
                      range.  If an integer, the lower bound of a
                      character range expressed as an integer.  May
                      also be a ``Range`` tuple, a ``CharSet`` or
                      ``FrozenCharSet``, or another sequence of items.
        :param end: If ``start`` is a string or an integer, this
                    parameter may be provided to specify the end of a
                    range.  If it is not provided, the range will
                    include only the single character specified by
                    ``start``.  This parameter is not meaningful for
                    other ``start`` types.
        """

        # Handle initialization
        if start is None and end is not None:
            # Special escape: initialize from a list of ranges
            super(CharSet, self).__init__(list(end))
        elif start is not None:
            if isinstance(start, six.integer_types):
                # Start and end must both be integers
                _vchars(start)
                if end is not None:
                    _vchars(end)
                    if start > end:
                        raise ValueError('invalid range "%c-%c"' %
                                         (start, end))
                super(CharSet, self).__init__([
                    Range(start, start if end is None else end),
                ])

            elif isinstance(start, six.string_types):
                # Start and end must both be strings (single
                # characters)
                if end is not None and start > end:
                    raise ValueError('invalid range "%c-%c"' % (start, end))
                super(CharSet, self).__init__([
                    Range(ord(start), ord(start if end is None else end)),
                ])

            elif isinstance(start, tuple):
                # Ensure a normal tuple gets converted to a range
                super(CharSet, self).__init__([Range(*start)])

            elif isinstance(start, BaseCharSet):
                # Copy another character set
                super(CharSet, self).__init__(list(start.ranges))

            else:
                # A sequence of items; add them all
                super(CharSet, self).__init__([])
                for item in start:
                    self.add(item)
        else:
            # Make an empty set
            super(CharSet, self).__init__([])

    def __iand__(self, other):
        """
        Generate the intersection between this character set and another,
        updating the contents of this one.

        :param other: Another object to compute an intersection with.

        :returns: A character set containing the intersection.
        :rtype: ``CharSet``
        """

        if isinstance(other, BaseCharSet):
            # Short cut the identical sets case
            if self != other:
                self.ranges = _intersection(self.ranges, other.ranges)
                self._len_cache = None
            return self
        return super(CharSet, self).__iand__(other)

    def __ior__(self, other):
        """
        Generate the union between this character set and another,
        updating the contents of this one.

        :param other: Another object to compute the union with.

        :returns: A character set containing the union.
        :rtype: ``CharSet``
        """

        if isinstance(other, BaseCharSet):
            # Short cut the identical sets case
            if self != other:
                self.ranges = _union(self.ranges, other.ranges)
                self._len_cache = None
            return self
        return super(CharSet, self).__ior__(other)

    def __isub__(self, other):
        """
        Generate the difference between this character set and another,
        updating the contents of this one.

        :param other: Another object to compute the difference with.

        :returns: A character set containing the difference.
        :rtype: ``CharSet``
        """

        if isinstance(other, BaseCharSet):
            # Short cut the identical sets case
            self.ranges = ([] if self == other
                           else _difference(self.ranges, other.ranges))
            self._len_cache = None
            return self
        return super(CharSet, self).__isub__(other)

    def __ixor__(self, other):
        """
        Generate the symmetric difference between this character set and
        another, updating the contents of this one.

        :param other: Another object to compute the symmetric
                      difference with.

        :returns: A character set containing the symmetric difference.
        :rtype: ``CharSet``
        """

        if isinstance(other, BaseCharSet):
            # Short cut the identical sets case
            self.ranges = ([] if self == other
                           else _sym_difference(self.ranges, other.ranges))
            self._len_cache = None
            return self
        return super(CharSet, self).__ixor__(other)

    def add(self, item):
        """
        Add an item to the character set.

        :param item: The character to add.  May be either a
                     1-character string or an integer.
        """

        # Convert string to integer
        if isinstance(item, six.string_types):
            item = ord(item)
        else:
            _vchars(item)

        # Look up the insertion point
        idx, contained = _search_ranges(self.ranges, item)
        if contained:
            # Item is already a member of the set
            return

        # The length of the set will be altered; invalidate the length
        # cache
        self._len_cache = None

        # Add the range
        _add_range(self.ranges, item, item, (idx, contained), (idx, contained))

    def discard(self, item):
        """
        Discard an item from the character set.

        :param item: The character to remove.  May be either a
                     1-character string or an integer.
        """

        # Convert string to integer
        if isinstance(item, six.string_types):
            item = ord(item)
        else:
            _vchars(item)

        # If the ranges are empty, do nothing
        if not self.ranges:
            return

        # Find the item in the ranges list
        idx, contained = _search_ranges(self.ranges, item)
        if not contained:
            # Item is already excluded, so nothing to do
            return

        # The length of the set will be altered; invalidate the length
        # cache
        self._len_cache = None

        # Remove the item
        _discard_range(self.ranges, item, item,
                       (idx, contained), (idx, contained))

    def remove(self, item):
        """
        Remove an item from the character set.

        :param item: The character to remove.  May be either a
                     1-character string or an integer.

        :raises KeyError:
            The specified item is not present in the character set.
        """

        # Convert string to integer
        if isinstance(item, six.string_types):
            char = ord(item)
        else:
            _vchars(item)
            char = item

        # If the ranges are empty, raise a KeyError
        if not self.ranges:
            raise KeyError(item)

        # Find the item in the ranges list
        idx, contained = _search_ranges(self.ranges, char)
        if not contained:
            # Item is already excluded, so raise KeyError; note we're
            # using what was originally passed in for item
            raise KeyError(item)

        # The length of the set will be altered; invalidate the length
        # cache
        self._len_cache = None

        # Remove the item
        _discard_range(self.ranges, item, item,
                       (idx, contained), (idx, contained))

    def pop(self):
        """
        Pop a character off the character set.

        :returns: The character popped from the character set.
        :rtype: ``str``
        """

        if not self.ranges:
            # Character set is empty
            raise KeyError()

        # Grab the first item and remove it
        item = self.ranges[0].start
        self._len_cache = None  # invalidate length cache
        _discard_range(self.ranges, item, item, (0, True), (0, True))

        return six.unichr(item)

    def clear(self):
        """
        Clear the character set.
        """

        # This is easy
        self.ranges = []
        self._len_cache = None  # invalidate length cache


class FrozenCharSet(BaseCharSet):
    """
    Represent a set of characters.  This differs from the standard
    Python ``set`` type by storing compact ranges of characters.  A
    ``disjoint()`` class method allows decomposition of several
    potentially overlapping character sets into disjoint (but possibly
    adjoining) character sets.
    """

    def __init__(self, start=None, end=None):
        """
        Initialize a ``CharSet`` instance.

        :param start: If a string, the lower bound of a character
                      range.  If an integer, the lower bound of a
                      character range expressed as an integer.  May
                      also be a ``Range`` tuple, a ``CharSet`` or
                      ``FrozenCharSet``, or another sequence of items.
        :param end: If ``start`` is a string or an integer, this
                    parameter may be provided to specify the end of a
                    range.  If it is not provided, the range will
                    include only the single character specified by
                    ``start``.  This parameter is not meaningful for
                    other ``start`` types.
        """

        # Handle initialization
        if start is None and end is not None:
            # Special escape: initialize from a list of ranges
            super(FrozenCharSet, self).__init__(tuple(end))
        elif start is not None:
            if isinstance(start, six.integer_types):
                # Start and end must both be integers
                _vchars(start)
                if end is not None:
                    _vchars(end)
                    if start > end:
                        raise ValueError('invalid range "%c-%c"' %
                                         (start, end))
                super(FrozenCharSet, self).__init__((
                    Range(start, start if end is None else end),
                ))

            elif isinstance(start, six.string_types):
                # Start and end must both be strings (single
                # characters)
                if end is not None and start > end:
                    raise ValueError('invalid range "%c-%c"' % (start, end))
                super(FrozenCharSet, self).__init__((
                    Range(ord(start), ord(start if end is None else end)),
                ))

            elif isinstance(start, tuple):
                # Ensure a normal tuple gets converted to a range
                super(FrozenCharSet, self).__init__((Range(*start),))

            elif isinstance(start, BaseCharSet):
                # Copy another character set
                super(FrozenCharSet, self).__init__(tuple(start.ranges))

            else:
                # A sequence of items; add them all, using a CharSet
                # temporarily (since a FrozenCharSet is immutable)
                tmp = CharSet(start, end)
                super(FrozenCharSet, self).__init__(tuple(tmp.ranges))
        else:
            # Make an empty set
            super(FrozenCharSet, self).__init__(())

    def __hash__(self):
        """
        Make a ``FrozenCharSet`` hashable.

        :returns: A hash code for the character set.
        :rtype: ``int``
        """

        return hash(self.ranges)
