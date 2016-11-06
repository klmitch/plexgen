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

import six

from plexgen import charset
from plexgen import states
from plexgen import transitions


_repeat_equiv = {
    '*': (0, None),
    '+': (1, None),
    '?': (0, 1),
}


class _StateMapper(dict):
    """
    A subclass of ``dict`` to help create states in the target
    machine.  This is used by ``Machine.copy()``.
    """

    def __init__(self, src, dest):
        """
        Initialize a ``_StateMapper`` instance.

        :param src: The source machine.
        :type src: ``Machine``
        :param dest: The destination machine.
        :type dest: ``Machine``
        """

        # Initialize with the machine's start states
        super(_StateMapper, self).__init__({src._start: dest._start})

        self.src = src
        self.dest = dest

    def __missing__(self, key):
        """
        Construct a new destination state on the fly, to correspond to a
        designated source state.

        :param key: The source state to construct a duplicate of.
        :type key: ``plexgen.states.State``

        :returns: A new destination state corresponding to the source
                  state.
        :rtype: ``plexgen.states.State``
        """

        # Construct the new destination state
        new = self.dest._new_state(key.accepting)

        # Save it to the mapping
        self[key] = new

        return new


class Machine(object):
    """
    Represent a generic finite state automaton.  This provides the
    basic routines for constructing an arbitrary FSA, including class
    methods to match character sets or strings, along with all the
    basic construction methods, such as ``concat()`` (``+`` operator),
    ``alternate()`` (``|`` operator) and ``repeat()`` (``*``
    operator).  Other methods of note: ``copy()`` creates a deep copy
    of the machine; ``reverse()`` reverses the machine in place; and
    ``dfa()`` constructs a new machine that is a deterministic finite
    automaton.
    """

    def __init__(self, accepting=False, code=None):
        """
        Initialize a ``Machine`` instance.

        :param bool accepting: A boolean indicating whether the start
                               state should also be an accepting
                               state.
        :param str code: A start code corresponding to the start
                         state.  Optional.
        """

        # The actual machine
        self._start = State(accepting, code)
        self._accepting = set([self._start] if accepting else [])
        self._states = set([self._start])

        # There could be multiple accepting states, but there are
        # places where we want a single final state; the _final
        # property will create a new state if necessary, and that
        # final state will be cached here
        self._final_cache = None

    def __len__(self):
        """
        The length of a machine is defined to be the number of states in
        the machine.

        :returns: The number of states in the machine.
        :rtype: ``int``
        """

        return len(self._states)

    def __iter__(self):
        """
        Iterate over all the states of the machine.  The start states are
        always the first states produced, and all accepting states
        (that are not start states) will always be produced last.

        :returns: A generator producing all the states of the machine.
        """

        # Select the start states to produce; this is a separate
        # method to allow Lexer to override.  The list is ordered, so
        # be careful to maintain the order when producing them...
        starts = set()
        for state in self._get_starts():
            starts.add(state)

            yield state

        # Set up the set of accepting states, not including the start
        # states, so we can skip them below
        lasts = self._accepting - starts

        # Produce the remaining states
        for state in self._states:
            # Only want the middle states for now
            if state in starts or state in lasts:
                continue

            yield state

        # Finally, produce the accepting states
        for state in lasts:
            yield state
    iter_states = __iter__

    def _new_state(self, accepting=False, code=None):
        """
        Construct a new state for the machine.

        :param bool accepting: If ``True``, indicates that the state
                               is an accepting state.
        :param str code: The start code to associate with a node.
                         Defaults to ``None``.

        :returns: The new state.
        :rtype: ``plexgen.states.State``
        """

        # Construct the new state
        new = states.State(accepting, code)

        # Add it to the set of machine states
        self._states.add(new)

        # If it's an accepting state, update the accepting set
        if new.accepting:
            self._accepting.add(new)
            self._final_cache = None  # invalidate cached _final

        return new

    def _add_start(self):
        """
        Adds a new start state to the machine, displacing the original.
        The new start state will have an epsilon transition to the
        original start state.

        :returns: The new start state.
        :rtype: ``plexgen.states.State``
        """

        # Create the new state
        new = self._new_state(self._start.accepting, self._start.code)

        # Make sure there's an epsilon transition
        new.transition(transitions.Epsilon, self._start)

        # Canonicalize the old state
        self._start.accepting = False
        self._start.code = None
        self._accepting.discard(self._start)

        # Make it the start node
        self._start = new

        return new

    def _unify_accepting(self):
        """
        Adds a new accepting state, adding epsilon transitions from the
        current set of accepting states to the new one.  The set of
        accepting states is updated to contain only the new accepting
        state.

        :returns: The new accepting state.
        :rtype: ``plexgen.states.State``
        """

        # Create the new state.  Don't set it accepting yet; we don't
        # want a spurious epsilon transition back to the state itself
        new = self._new_state()

        # Create the epsilon transitions from the existing accepting
        # states
        for state in self._accepting:
            state.transition(transitions.Epsilon, new)

            # Clear their accepting flag, since they're not accepting
            # states anymore
            state.accepting = False

        # Update the accepting set
        new.accepting = True
        self._accepting = set([new])
        self._final_cache = new  # avoid recomputation later

        return new

    def _get_starts(self):
        """
        Retrieve a list of all the start states.

        :returns: A properly ordered list of start states.
        :rtype: ``list``
        """

        return [self._start]

    def copy(self):
        """
        Construct a duplicate of this machine.

        :returns: An independent duplicate of the machine.
        :rtype: ``Machine``
        """

        # First step is to just create the new machine
        mach = self.__class__()

        # Make sure to copy over the accepting status and start code
        # of the start state
        mach._start.code = self._start.code
        if self._start.accepting:
            mach._start.accepting = True
            mach._accepting.add(mach._start)

        # Need to maintain a mapping between our states and the new
        # machine's states
        state_map = _StateMapper(self, mach)

        # Duplicate all the transitions
        for state in self._states:
            for trans in state.iter_out():
                state_map[state].transition(
                    trans.__class__,
                    state_map[trans.state_in],
                    **trans.args
                )

        return mach

    def reverse(self):
        """
        Reverse the machine.  This alters this machine to run the match
        backwards.

        :returns: The altered machine.
        :rtype: ``Machine``
        """

        # Grab the start and final states
        start = self._start
        final = self._final  # may call _unify_accepting() implicitly

        # Reverse each state and its transitions
        for state in self._states:
            for trans in state.iter_out():
                trans.reverse()
            state.reverse()

        # Now we have to swap the meaning of the start and final
        # states.  Note that the start state could be a final state as
        # well, so act accordingly
        if start is not final:
            # Handle swapping accepting state
            self._start = final
            final.accepting = False
            start.accepting = True
            self._accepting = set([start])

            # Now handle the code
            final.code = start.code
            start.code = None

        return self

    def dfa(self):
        """
        Construct a deterministic finite automaton from this machine.

        :returns: A new machine without any epsilon transitions or
                  ambiguous match transitions.
        :rtype: ``Machine``
        """

        # Create the new machine
        mach = self.__class__()

        # Initialize our state map and our work queue
        start = states.eps_closure(self._start)
        state_map = {start: mach._start}
        workq = [start]

        # Make sure to set the machine's start state to be accepting,
        # if necessary
        if start & self._accepting:
            mach._start.accepting = True
            mach._accepting.add(mach._start)

        while workq:
            state = workq.pop()

            # Compute the transition table, a dictionary of lists
            # keyed by the transition class
            trans_tab = {}
            for substate in state:
                for trans in substate.iter_out():
                    # Skip epsilon transitions; we have those
                    if isinstance(trans, transitions.Epsilon):
                        continue

                    trans_tab.setdefault(trans.__class__, [])
                    trans_tab[trans.__class__].append(trans)

            # Build a disjoint transition set
            for cls, trans_list in trans_tab.items():
                for trans in cls.disjoint(trans_list):
                    # Assemble the closure of reachable states for
                    # this disjoint transition
                    closure = states.eps_closure(*(t.state_in for t in trans))

                    # Build a new DFA state if necessary
                    if closure not in state_map:
                        state_map[closure] = mach._new_state(
                            closure & self._accepting)
                        workq.append(closure)

                    # Add the DFA state transition
                    state_map[state].transition(
                        cls, state_map[closure], **trans[0].args
                    )

        return mach

    @property
    def _final(self):
        """
        Return the final state.  This property may update the machine by
        adding a single new accepting state, but only if there are
        more than one accepting states currently.
        """

        # Is it cached?
        if self._final_cache is None:
            if not self._accepting:
                # If there are no accepting states, just return None
                return None

            elif len(self._accepting) > 1:
                # Only unify if we need to
                self._final_cache = self._unify_accepting()

            else:
                # Exactly one accepting state
                self._final_cache = list(self._accepting)[0]

        return self._final_cache


class Matcher(Machine):
    """
    A subclass of ``Machine`` that includes support for string
    matching behavior.  This class also provides the necessary
    primitives for implementing Thompson's Construction.
    """

    @classmethod
    def match_cset(cls, start, end=None):
        """
        Constructs a ``Matcher`` instance that matches a character set.

        :param start: Either a character set or the starting point of
                      a character set range, expressed as either an
                      integer code point or the character string
                      itself.  Character sets must be
                      ``plexgen.charset.CharSet`` instances.
        :param end: If ``start`` is a ``plexgen.charset.CharSet``
                    instance, ignored; otherwise, passed as the second
                    parameter of ``plexgen.charset.CharSet``
                    expressing the end of the character range started
                    by ``start``.  This must be the same type (integer
                    or character) as ``start``.  If omitted, the
                    constructed character set will contain only
                    ``start``.

        :returns: The desired machine.
        :rtype: ``Matcher``
        """

        # Construct the character set
        if not isinstance(start, charset.CharSet):
            start = charset.CharSet(start, end)

        # Construct the machine with one transition
        mach = cls()
        final = mach._new_state(True)
        mach._start.transition(transitions.MatchChar, final, cset=start)

        return mach

    @classmethod
    def match_str(cls, string):
        """
        Constructs a ``Matcher`` instance that matches a string.

        :param string: The string to match.

        :returns: The desired machine.
        :rtype: ``Matcher``
        """

        # Initialize the machine
        mach = cls()

        # Add transitions for each character in the string
        last_state = mach._start
        for i, char in enumerate(string):
            state = mach._new_state(i == len(string) - 1)
            last_state.transition(transitions.MatchChar, final,
                                  cset=charset.CharSet(char))
            last_state = state

        return mach

    def __init__(self):
        """
        Initialize a ``Matcher`` instance.
        """

        # Note: this exists to block the extra arguments to
        # Machine.__init__()
        super(Matcher, self).__init__()

    def __add__(self, other):
        """
        Constructs the concatenation of this machine with another machine.
        Both operands are left unaltered.

        :param other: The other machine to concatenate.
        :type other: ``Matcher``

        :returns: A concatenated machine.
        :rtype: ``Matcher``
        """

        # Only implemented between two Matcher instances
        if not isinstance(other, Matcher):
            return NotImplemented

        # Copy both ourself and the other to avoid altering the
        # operands
        return self.copy().concat(other.copy())

    def __iadd__(self, other):
        """
        Concatenates another machine to this machine.  The other machine
        is left unaltered.

        :param other: The other machine to concatenate.
        :type other: ``Matcher``

        :returns: A concatenated machine.
        :rtype: ``Matcher``
        """

        # Only implemented between two Matcher instances
        if not isinstance(other, Matcher):
            return NotImplemented

        # Copy the other to avoid altering it
        return self.concat(other.copy())

    def __or__(self, other):
        """
        Constructs a machine that matches either what this machine matches
        or what the other machine matches.  Both operands are left
        unaltered.

        :param other: The other machine to alternate.
        :type other: ``Matcher``

        :returns: An alternation machine.
        :rtype: ``Matcher``
        """

        # Only implemented between two Matcher instances
        if not isinstance(other, Matcher):
            return NotImplemented

        # Copy both ourself and the other to avoid altering the
        # operands
        return self.copy().alternate(other.copy())

    def __ior__(self, other):
        """
        Constructs a machine that matches either what this machine matches
        or what the other machine matches.  The other machine is left
        unaltered.

        :param other: The other machine to alternate.
        :type other: ``Matcher``

        :returns: An alternation machine.
        :rtype: ``Matcher``
        """

        # Only implemented between two Matcher instances
        if not isinstance(other, Matcher):
            return NotImplemented

        # Copy the other to avoid altering the operands
        return self.alternate(other.copy())

    def __mul__(self, other):
        """
        Constructs a machine that matches what this machine matches, but
        some number of times other than once--i.e, 0 or more, 1 or
        more, 0 or 1, etc.  This machine is left unaltered.

        :param other: An instruction for how often to match.  This may
                      be an integer ("match _n_ times"), a tuple of
                      integers ("match between _m_ and _n_ times"), or
                      the special characters '*' ("match 0 or more
                      times"), '+' ("match 1 or more times"), or '?'
                      ("match 0 or 1 times").  For tuple ranges, the
                      range may be made open-ended by making one of
                      the elements ``None``.  The character '*' is
                      equivalent to ``(0, None)``, '+' to ``(1,
                      None)``, and '?' to ``(0, 1)``.

        :returns: A multi-match machine.
        :rtype: ``Matcher``
        """

        try:
            # Copy ourself to avoid alterations
            return self.copy().repeat(other)
        except TypeError:
            return NotImplemented

    def __imul__(self, other):
        """
        Constructs a machine that matches what this machine matches, but
        some number of times other than once--i.e, 0 or more, 1 or
        more, 0 or 1, etc.  This machine is altered in place.

        :param other: An instruction for how often to match.  This may
                      be an integer ("match _n_ times"), a tuple of
                      integers ("match between _m_ and _n_ times"), or
                      the special characters '*' ("match 0 or more
                      times"), '+' ("match 1 or more times"), or '?'
                      ("match 0 or 1 times").  For tuple ranges, the
                      range may be made open-ended by making one of
                      the elements ``None``.  The character '*' is
                      equivalent to ``(0, None)``, '+' to ``(1,
                      None)``, and '?' to ``(0, 1)``.

        :returns: A multi-match machine.
        :rtype: ``Matcher``
        """

        try:
            # Copy ourself to avoid alterations
            return self.repeat(other)
        except TypeError:
            return NotImplemented

    def concat(self, other):
        """
        Concatenates another machine to this machine.  The other machine
        will be altered and should be discarded after this operation.

        :param other: The other machine to concatenate.
        :type other: ``Matcher``

        :returns: A concatenated machine.
        :rtype: ``Matcher``
        """

        # Can't concatenate anything other than a machine
        if not isinstance(other, Matcher):
            raise TypeError('cannot concatenate %s object' %
                            other.__class__.__name__)

        # Merge the state sets
        self._states |= other._states

        # Add an epsilon transition from our current final state to
        # the other machine's start state
        self._final.transition(transitions.Epsilon, other._start)

        # Update the accepting states
        self._final.accepting = False
        self._accepting = other._accepting
        self._final_cache = None  # invalidate cached _final

        return self

    def alternate(self, other):
        """
        Constructs a machine that matches either what this machine matches
        or what the other machine matches.  The other machine will be
        altered and should be discarded after this operation.

        :param other: The other machine to alternate.
        :type other: ``Matcher``

        :returns: An alternation machine.
        :rtype: ``Matcher``
        """

        # Can't alternate anything other than a machine
        if not isinstance(other, Matcher):
            raise TypeError('cannot alternate %s object' %
                            other.__class__.__name__)

        # Alter our start state to only have epsilon transitions out
        if not self._start.eps_out:
            self._add_start()

        # Similarly with our final state
        if not self._final.eps_in:
            self._unify_accepting()

        # Merge the state sets
        self._states |= other._states

        # Add epsilon transitions from our start state to the other
        # machine's start state, and similarly for the final state
        self._start.transition(Epsilon, other._start)
        other._final.transition(Epsilon, self._final)

        # Make sure to clear the accepting flag on the other machine's
        # final state
        other._final.accepting = False

        return self

    def repeat(self, other):
        """
        Constructs a machine that matches what this machine matches, but
        some number of times other than once--i.e, 0 or more, 1 or
        more, 0 or 1, etc.  This machine is altered in place.

        :param other: An instruction for how often to match.  This may
                      be an integer ("match _n_ times"), a tuple of
                      integers ("match between _m_ and _n_ times"), or
                      the special characters '*' ("match 0 or more
                      times"), '+' ("match 1 or more times"), or '?'
                      ("match 0 or 1 times").  For tuple ranges, the
                      range may be made open-ended by making one of
                      the elements ``None``.  The character '*' is
                      equivalent to ``(0, None)``, '+' to ``(1,
                      None)``, and '?' to ``(0, 1)``.

        :returns: A multi-match machine.
        :rtype: ``Matcher``
        """

        # Canonicalize other
        if isinstance(other, six.integer_types):
            # Single integer is equivalent to (n, n)
            min_cnt = other
            max_cnt = other
        elif other in _match_equiv:
            # One of the special repeat operators
            min_cnt, max_cnt = _repeat_equiv[other]
        elif isinstance(other, (list, tuple)) and len(other) == 2:
            # Tuple of (lower bound, upper bound)
            min_cnt, max_cnt = other

            # Min count of None is equivalent to 0
            if min_cnt is None:
                min_cnt = 0

            # Sanity-check the min count
            if not isinstance(min_cnt, six.integer_types) or min_cnt < 0:
                raise ValueError('invalid lower bound %r' % min_cnt)

            # Sanity-check the max count
            if (max_cnt is not None and
                    (not isinstance(max_cnt, six.integer_types) or
                     max_cnt < min_cnt)):
                raise ValueError('invalid upper bound %r' % max_cnt)
        else:
            # Don't understand that value
            raise TypeError('cannot understand repeat instruction %r' % other)

        # Figure out how many machines we need
        total = max(min_cnt, 1) if max_cnt is None else max_cnt

        # Make sure we have a single final state, so that ends up in
        # the copies and doesn't have to be created each time
        if len(self._accepting) > 1:
            self._unify_accepting()

        # Construct the copies we need
        machs = [self] + [self.copy() for _i in range(1, total)]

        # Now step through all the machines
        for i, mach in enumerate(machs):
            # If it's the last machine and we have an open interval,
            # make it repeat
            if i == len(machs) - 1 and max_cnt is None:
                mach._final.transition(transitions.Epsilon, mach._start)

            # If it's an optional machine, make it optional
            if i >= min_cnt:
                # Adds additional epsilon-only nodes at the beginning
                # and ending, if needed
                start = (mach._start if mach._start.eps_out
                         else mach._add_start())
                final = (mach._final if mach._final.eps_in
                         else mach._unify_accepting())

                # Add the transition that makes it optional
                start.transition(transitions.Epsilon, final)

            # Finally, concatenate the machine
            if mach is not self:
                self.concat(mach)

        return self


class Lexer(Machine):
    """
    A subclass of ``Machine`` that includes lexer-like behavior.  In
    particular, the start state is an accepting state, and machines
    can be added using the ``action()`` method, which creates a
    special ``Action`` transition back to the start state.
    """

    def __init__(self):
        """
        Initialize a ``Lexer`` instance.
        """

        # Initialize superclass
        super(Lexer, self).__init__(True, '')

        # Set up the index of start codes
        self._start_codes = {'': self._start}

    def _get_start_by_code(self, code):
        """
        Retrieve the start state for the given start code.

        :param str code: The start code to look up the start state
                         for.

        :returns: The appropriate start state, possibly just created.
        :rtype: ``plexgen.states.State``
        """

        if code not in self._start_codes:
            # Have to create a new one
            self._start_codes[code] = self._new_state(True, code)

        return self._start_codes[code]

    def _get_starts(self):
        """
        Retrieve a list of all the start states.  The list will be ordered
        by the start code name.

        :returns: A properly ordered list of start states.
        :rtype: ``list``
        """

        return [state for code, state in
                sorted(self._start_codes.items(), key=lambda x: x[0])]

    def action(self, mach, action, precedence, code='', exit_code=None,
               name=None):
        """
        Create a new action to be taken when a given submachine matches.

        :param mach: A machine that, when it accepts, should generate
                     an action.  The machine passed to this argument
                     will be altered, and should be discarded after
                     this operation.
        :type mach: ``Matcher``
        :param str action: The text of an action to execute when
                           ``mach`` matches.
        :param int precedence: The precedence of the action.  Smaller
                               values win out over larger values.  If
                               two machines match the same text, the
                               precedence is used to determine which
                               action to take.
        :param str code: The start code associated with the machine.
                         Defaults to the empty string.
        :param str exit_code: The start code to exit to.  This is used
                              to have a machine switch to a new start
                              code.  Defaults to be the same as
                              ``code``.
        :param str name: An optional name for the action.  This is
                         used for diagnostic purposes.

        :returns: The ``Lexer`` instance, for convenience.
        :rtype: ``Lexer``
        """

        # Add the machine states
        self._states |= mach._states

        # Pick the correct start nodes
        start = self._get_start_by_code(code)
        final = (start if exit_code is None
                 else self._get_start_by_code(exit_code))

        # Add an epsilon transition from the start state
        start.transition(transitions.Epsilon, mach._start)

        # Add an action transition from the machine's final state to
        # the designated start state
        mach._final.transition(transitions.Action, final,
                               action=action, precedence=precedence, name=name)

        # It's no longer an accepting state
        mach._final.accepting = False

        return self
