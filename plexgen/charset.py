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

import collections

import six

from plexgen import prioq


MIN_CHAR = 0
MAX_CHAR = 0x10ffff


Range = collections.namedtuple('Range', ['start', 'end'])


class CharSet(collections.MutableSet):
    """
    Represent a set of characters.  This differs from the standard
    Python ``set`` type by storing compact ranges of characters.  A
    ``disjoint()`` class method allows decomposition of several
    potentially overlapping character sets into disjoint (but possibly
    adjoining) character sets.
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

    def __init__(self, start=None, end=None):
        """
        Initialize a ``CharSet`` instance.

        :param start: If a string, the lower bound of a character
                      range.  If an integer, the lower bound of a
                      character range expressed as an integer.  May
                      also be a ``Range`` tuple, or a sequence of
                      items.
        :param end: If ``start`` is a string or an integer, this
                    parameter may be provided to specify the end of a
                    range.  If it is not provided, the range will
                    include only the single character specified by
                    ``start``.  This parameter is not meaningful for
                    other ``start`` types.
        """

        # Initialize the ranges list
        self.ranges = []

        # Handle initialization
        if start is not None:
            if isinstance(start, six.integer_types):
                # Start and end must both be integers
                self.ranges.append(Range(start, start if end is None else end))

            elif isinstance(start, six.string_types):
                # Start and end must both be strings (single
                # characters)
                self.ranges.append(Range(
                    ord(start), ord(start if end is None else end)
                ))

            elif isinstance(start, tuple):
                # Ensure a normal tuple gets converted to a range
                self.ranges.append(Range(*start))

            else:
                # A sequence of items; add them all
                for item in start:
                    self.add(item)

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

        return self._search_ranges(item)[1]

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
        """

        return sum((rng.end - rng.start) + 1
                   for rng in self.ranges)

    def _search_ranges(self, item):
        """
        Search the ``ranges`` list of a ``CharSet`` for the given item.
        This is implemented using a binary search.

        :param int item: The code point of the item to locate.

        :returns: A 2-tuple, where the first element specifies the
                  index of a range containing ``item`` or a location
                  in the ``ranges`` list where one could be inserted;
                  the second element is a boolean indicating whether
                  the item was found.
        """

        # Note: Adapted from standard Python "bisect" library, but
        # with additions due to the fact that we're storing ranges of
        # items, not the items themselves.

        # If there are no ranges, we have our answer
        if not self.ranges:
            return 0, False

        # Initialize the bisection variables
        lo = 0
        hi = len(self.ranges)
        while lo < hi:
            mid = (lo + hi) // 2

            if self.ranges[mid].start <= item <= self.ranges[mid].end:
                # Item is contained in a range at the midpoint
                return mid, True

            elif item < self.ranges[mid].start:
                # Item is to the left
                hi = mid

            else:
                # Item is to the right
                lo = mid + 1

        # Never hit a range containing the item, so return insertion
        # point
        return lo, False

    def add(self, item):
        """
        Add an item to the character set.

        :param item: The character to add.  May be either a
                     1-character string or an integer.
        """

        # Convert string to integer
        if isinstance(item, six.string_types):
            item = ord(item)

        # Look up the insertion point
        idx, contained = self._search_ranges(item)
        if contained:
            # Item is already a member of the set
            return

        # Find the start and end of the non-contained range
        start = self.ranges[idx - 1].end if idx > 0 else MIN_CHAR
        end = self.ranges[idx].start if idx < len(self.ranges) else MAX_CHAR

        # Figure out where the new item should go
        if item == start + 1:
            # Replace the range before the insertion point
            repl_idx = idx - 1
            replacement = Range(self.ranges[repl_idx].start, item)
            start += 1
        elif item == end - 1:
            # Replace the range at the insertion point
            repl_idx = idx
            replacement = Range(item, self.ranges[repl_idx].end)
            end -= 1
        else:
            # New item is smack dab in the middle of the non-contained
            # range, so just insert a new range
            self.ranges.insert(idx, Range(item, item))
            return

        # Do the ranges on either side of the index now overlap?
        if start + 1 == end:
            # Replace both ranges with a new one
            self.ranges[idx - 1:idx + 1] = [
                Range(self.ranges[idx - 1].start, self.ranges[idx].end),
            ]
        else:
            # Just make the replacement we determined above
            self.ranges[repl_idx] = replacement

    def discard(self, item):
        """
        Discard an item from the character set.

        :param item: The character to remove.  May be either a
                     1-character string or an integer.
        """

        # If the ranges are empty, do nothing
        if not self.ranges:
            return

        # Convert string to integer
        if isinstance(item, six.string_types):
            item = ord(item)

        # Find the item in the ranges list
        idx, contained = self._search_ranges(item)
        if not contained:
            # Item is already excluded, so nothing to do
            return

        # If item is one of the extreme points, just reconstruct the
        # range
        if self.ranges[idx].start == item and self.ranges[idx].end == item:
            # Eliminate the whole range
            del self.ranges[idx]
        elif self.ranges[idx].start == item:
            # Item is at the start of the range
            self.ranges[idx] = Range(self.ranges[idx].start + 1,
                                     self.ranges[idx].end)
        elif self.ranges[idx].end == item:
            # Item is at the end of the range
            self.ranges[idx] = Range(self.ranges[idx].start,
                                     self.ranges[idx].end - 1)
        else:
            # Item is in the middle of the range, so split it in two
            self.ranges[idx:idx + 1] = [
                Range(self.ranges[idx].start, item - 1),
                Range(item + 1, self.ranges[idx].end),
            ]
