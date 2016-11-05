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


def _all_eps(trans_tab):
    """
    Determine if all transitions in the transitions table are
    ``plexgen.transitions.Epsilon`` transitions.
    ``plexgen.transitions.Epsilon`` transitions, by definition, have
    priority 0.

    :param dict trans_tab: A transitions table.  This is a ``dict`` of
                           ``set``s, keyed by the transition priority.
                           The sets contain the actual transitions.

    :returns: A ``True`` value indicates that the transitions table
              contains only ``plexgen.transitions.Epsilon``
              transitions.
    """

    for prio, trans_set in trans_tab.items():
        if prio == 0:
            # Priority 0 transitions are Epsilons, by definition
            continue

        if trans_set:
            return False

    return True


def _iter_trans(trans_tab, prio):
    """
    Iterate over transitions in the transitions table.

    :param dict trans_tab: A transitions table.  This is a ``dict`` of
                           ``set``s, keyed by the transition priority.
                           The sets contain the actual transitions.
    :param prio: The priority level to iterate over.  If ``None``, all
                 transitions will be iterated over.

    :returns: An iterator over the desired transitions.  Iteration
              will be ordered by priority, from lowest to highest; the
              order of transitions with the same priority is
              undefined.
    """

    # Priorities to iterate over
    prios = sorted(trans_tab.keys()) if prio is None else [prio]
    for prio in prios:
        for trans in trans_tab.get(prio, set()):
            yield trans


def eps_closure(states):
    """
    Given an iterable of states, constructs a ``frozenset`` of states
    reachable by ``Epsilon`` transitions.

    :param states: An iterable of states.

    :returns: The states reachable by ``Epsilon`` transitions.
    :rtype: ``frozenset``
    """

    # Construct the work queue and visited set
    workq = list(states)
    visited = set()

    # And the result set
    states = set(states)

    while workq:
        # Pick a state off the queue
        state = workq.pop(0)

        # Remember the visit
        visited.add(state)

        # Traverse its outgoing epsilon transitions
        for trans in state.iter_out(0):
            if trans.state_in in visited:
                # Already visited that state; note that the Python
                # optimizer may optimize away the continue
                continue  # pragma: no cover

            # OK, found a new state; add it to the result set and
            # ensure we visit it too
            states.add(trans.state_in)
            workq.append(trans.state_in)

    # Convert to a frozenset so it can be hashed
    return frozenset(states)


class State(object):
    """
    Represent an automaton state.  States remember the transitions in
    and out of the state.
    """

    def __init__(self, accepting=False, code=None):
        """
        Initialize a ``State`` instance.

        :param bool accepting: A boolean indicating whether the state
                               is an accepting state.

        :param str code: A start code associated with the state.
                         Defaults to ``None``.
        """

        self.accepting = bool(accepting)
        self.code = code

        # Most of the languages will want to assign some name to the
        # states, whether it be an integer index or an actual name.
        # Just initialize it to None for now...
        self.name = None

        # The transition tables.  Keys are transition priority levels,
        # and values are sets of transitions.
        self._trans_in = {}
        self._trans_out = {}

        # Cache for the results of eps_in and eps_out
        self._eps_in = None
        self._eps_out = None

    def reverse(self):
        """
        Reverse the direction of the state.  This swaps the transition
        tables, and is used as part of the DFA minimization process.
        Note that calling this method alone is insufficient to reverse
        the automaton; the transitions themselves must also be
        reversed.
        """

        self._trans_in, self._trans_out = self._trans_out, self._trans_in

    def transition(self, trans_class, next_state, **kwargs):
        """
        Add a transition to another state.  Note that transition merge
        logic may alter another existing transition, rather than
        creating a new one.

        :param trans_class: The class of the transition.
        :type trans_class: ``plexgen.transitions.Transition`` subclass
        :param next_state: The state to transition to.
        :type next_state: ``State``
        :param **kwargs: Keyword arguments to be passed to the
                         ``trans_class`` constructor.
        """

        # Construct the new transition
        trans = trans_class(self, next_state, **kwargs)

        # Add it to the states; begin by initializing the transition
        # priority buckets in both states
        self._trans_out.setdefault(trans.priority, set())
        next_state._trans_in.setdefault(trans.priority, set())

        # Find all similar transitions between us and next_state
        others = set([
            t for t in self._trans_out[trans.priority]
            if t.state_in is next_state and t.__class__ is trans.__class__
        ])

        # Now, can the transition be merged?
        update = trans.merge(others)
        if update is None:
            # Can't merge, just add the transition
            self._trans_out[trans.priority].add(trans)
            next_state._trans_in[trans.priority].add(trans)
        else:
            # We've merged; remove others from the existing
            # transitions
            self._trans_out[trans.priority] -= others
            next_state._trans_in[trans.priority] -= others

            # Now apply the merged update
            self._trans_out[trans.priority] |= update
            next_state._trans_in[trans.priority] |= update

        # Adding transitions invalidates the _eps_{in,out} caches
        next_state._eps_in = None
        self._eps_out = None

    def iter_in(self, prio=None):
        """
        Iterate over all transitions to this state.

        :param prio: The transition priorities to iterate over.
                     Defaults to ``None``, meaning to iterate over all
                     transitions.

        :returns: An iterator over the desired transitions.  Iteration
                  will be ordered by priority, from lowest to highest;
                  the order of transitions with the same priority is
                  undefined.
        """

        return _iter_trans(self._trans_in, prio)

    def iter_out(self, prio=None):
        """
        Iterate over all transitions from this state.

        :param prio: The transition priorities to iterate over.
                     Defaults to ``None``, meaning to iterate over all
                     transitions.

        :returns: An iterator over the desired transitions.  Iteration
                  will be ordered by priority, from lowest to highest;
                  the order of transitions with the same priority is
                  undefined.
        """

        return _iter_trans(self._trans_out, prio)

    @property
    def eps_in(self):
        """
        A property that is ``True`` if and only if all incoming
        transitions are ``plexgen.transitions.Epsilon`` transitions.
        """

        if self._eps_in is None:
            self._eps_in = _all_eps(self._trans_in)

        return self._eps_in

    @property
    def eps_out(self):
        """
        A property that is ``True`` if and only if all outgoing
        transitions are ``plexgen.transitions.Epsilon`` transitions.
        """

        if self._eps_out is None:
            self._eps_out = _all_eps(self._trans_out)

        return self._eps_out
