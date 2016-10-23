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

import heapq


class KeyWrap(object):
    """
    Wraps an object with a key routine.  Comparisons are performed by
    using the result of calling the key routine on the object.  This
    allows complex key routines to be used with the standard Python
    ``heapq`` operations.
    """

    __slots__ = ['obj', 'key']

    def __init__(self, obj, key):
        """
        Initialize a ``KeyWrap`` instance.

        :param obj: The object to be wrapped.
        :param key: The key routine for the object.
        """

        self.obj = obj
        self.key = key

    def __eq__(self, other):
        """
        Compare for equality.

        :param other: Another object to compare to.  If it's another
                      ``KeyWrap`` object, compares the keys.

        :returns: The result of the comparison.
        :rtype: ``bool``
        """

        if isinstance(other, KeyWrap):
            return self.key(self.obj) == other.key(other.obj)
        return self.key(self.obj) == other

    def __ne__(self, other):
        """
        Compare for inequality.

        :param other: Another object to compare to.  If it's another
                      ``KeyWrap`` object, compares the keys.

        :returns: The result of the comparison.
        :rtype: ``bool``
        """

        if isinstance(other, KeyWrap):
            return self.key(self.obj) != other.key(other.obj)
        return self.key(self.obj) != other

    def __lt__(self, other):
        """
        Compare for less than.

        :param other: Another object to compare to.  If it's another
                      ``KeyWrap`` object, compares the keys.

        :returns: The result of the comparison.
        :rtype: ``bool``
        """

        if isinstance(other, KeyWrap):
            return self.key(self.obj) < other.key(other.obj)
        return self.key(self.obj) < other

    def __le__(self, other):
        """
        Compare for less than or equal to.

        :param other: Another object to compare to.  If it's another
                      ``KeyWrap`` object, compares the keys.

        :returns: The result of the comparison.
        :rtype: ``bool``
        """

        if isinstance(other, KeyWrap):
            return self.key(self.obj) <= other.key(other.obj)
        return self.key(self.obj) <= other

    def __gt__(self, other):
        """
        Compare for greater than.

        :param other: Another object to compare to.  If it's another
                      ``KeyWrap`` object, compares the keys.

        :returns: The result of the comparison.
        :rtype: ``bool``
        """

        if isinstance(other, KeyWrap):
            return self.key(self.obj) > other.key(other.obj)
        return self.key(self.obj) > other

    def __ge__(self, other):
        """
        Compare for greater than or equal to.

        :param other: Another object to compare to.  If it's another
                      ``KeyWrap`` object, compares the keys.

        :returns: The result of the comparison.
        :rtype: ``bool``
        """

        if isinstance(other, KeyWrap):
            return self.key(self.obj) >= other.key(other.obj)
        return self.key(self.obj) >= other


class PrioQ(object):
    """
    Implements a priority queue as a thin wrapper around the standard
    Python ``heapq`` operations.  Uses ``KeyWrap`` to allow the use of
    complex key routines with objects.
    """

    __slots__ = ['items', 'key']

    def __init__(self, items=None, key=lambda x: x):
        """
        Initialize a ``PrioQ`` instance.

        :param items: An optional list of items to initialize the
                      queue with.
        :type items: ``list``
        :param key: The key routine to use for ordering.  Similar in
                    concept to the ``key`` parameter to the
                    ``sorted()`` built-in.
        """

        self.items = [KeyWrap(i, key) for i in (items or [])]
        self.key = key
        heapq.heapify(self.items)

    def __bool__(self):
        """
        Convert a ``PrioQ`` instance to boolean.

        :returns: A ``True`` value if there are items in the queue,
                  ``False`` otherwise.
        :rtype: ``bool``
        """

        return bool(self.items)
    __nonzero__ = __bool__

    def push(self, *items):
        """
        Push one or more items onto the priority queue.

        :param *items: Items to be pushed onto the queue.
        """

        for item in items:
            heapq.heappush(self.items, KeyWrap(item, self.key))

    def pop(self):
        """
        Pop and return one item off the priority queue.  To examine the
        top item from the queue without removing it, use the ``top``
        property.

        :returns: The top item from the priority queue.
        """

        return heapq.heappop(self.items).obj

    @property
    def top(self):
        """
        Retrieve the top item off the priority queue.  Note: Do not make
        alterations to the item without removing it from the queue
        first, in order to maintain the heap property.
        """

        return self.items[0].obj
