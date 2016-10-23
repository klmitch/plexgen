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

import six

from plexgen import charset


@six.add_metaclass(abc.ABCMeta)
class Transition(object):
    """
    An abstract base class for all transitions.  A transition moves
    from one state of an automaton to another.
    """

    # Defaults for transition arguments.
    defaults = {}

    # Note: in Python 2, @abc.abstractmethod wrapped in @classmethod
    # does not actually create an abstract method, thus leaving this
    # method out would not prevent a subclass from being instantiated.
    # In Python 3, an abstract class method *is* created.
    @classmethod
    @abc.abstractmethod
    def disjoint(cls, transitions):
        """
        Given a list of transitions, this class method must create a new
        list of disjoint transitions that will transition between the
        same set of states.

        :param list transitions: A list of ``Transition`` instances.

        :returns: An iterator that produces lists of disjoint
                  transitions.  Note that this is essentially a list
                  of lists, where each element of the inner list is a
                  ``Transition`` instance.
        """

        pass  # pragma: no cover

    def __init__(self, state_out, state_in, **kwargs):
        """
        Initialize a ``Transition`` instance.

        :param state_out: The origin state for the transition.
        :type state_out: ``plexgen.states.State``
        :param state_in: The destination state for the transition.
        :type state_in: ``plexgen.states.State``
        :param **kwargs: Extra keyword arguments for the transition.
                         These are used to control when the transition
                         is made, or what action to perform when the
                         transition is taken.
        """

        # Build the transition arguments, taking into account any
        # defaults
        args = self.defaults.copy()
        args.update(kwargs)

        # Check if any required arguments are missing
        missing = self.trans_args - set(args.keys())
        if missing:
            raise TypeError('missing required keyword arguments: "%s"' %
                            '", "'.join(arg for arg in sorted(missing)))

        # Check if there are any extra arguments
        extra = set(args.keys()) - self.trans_args
        if extra:
            raise TypeError('unknown extra keyword arguments: "%s"' %
                            '", "'.join(arg for arg in sorted(extra)))

        # Save the arguments
        self.state_out = state_out
        self.state_in = state_in
        self.args = args

    def __getattr__(self, attr):
        """
        Retrieve keyword arguments passed to the constructor.

        :param str attr: The name of the keyword argument to retrieve.

        :returns: The value of the designated keyword argument.
        """

        try:
            return self.args[attr]
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, attr))

    def reverse(self):
        """
        Reverse the direction of the transition.  This swaps the states of
        the transition, and is used as part of the DFA minimization
        process.  Note that calling this method alone is insufficient
        to reverse the automaton; the states must also be reversed.
        """

        self.state_out, self.state_in = self.state_in, self.state_out

    @abc.abstractmethod
    def match(self, char, sim):
        """
        Determine if the character is matched by this transition.  Used
        when simulating the automaton.

        :param str char: The character to match, or ``None`` at the
                         end of the string.
        :param sim: The simulator.  This may be used to access
                    simulation state information, such as the lexeme
                    being processed.
        :type sim: ``plexgen.simulator.Simulator``

        :returns: A ``True`` value if the transition was matched.
                  Note that it is the transition's responsibility to
                  call the ``sim.consume()`` method if the character
                  is to be consumed.
        :rtype: ``bool``
        """

        pass  # pragma: no cover

    @abc.abstractmethod
    def merge(self, others):
        """
        Given a set of other transitions between the same two states,
        merge all the transitions (including this one) into the
        smallest possible set.

        :param set others: A set of ``Transition`` instances with the
                           same priority.

        :returns: Either a new ``set`` containing merged
                  ``Transition`` instances, or ``None`` if merging is
                  not possible.
        """

        pass  # pragma: no cover

    @abc.abstractproperty
    def trans_args(self):
        """
        The ``set`` of required transition keyword argument names.  This
        should be the full list; to provide defaults for some
        arguments, override the ``defaults`` class attribute with a
        dictionary mapping those argument names to the appropriate
        default.
        """

        pass  # pragma: no cover

    @abc.abstractproperty
    def priority(self):
        """
        Some transitions should be checked before others--for instance,
        it's probably desired to check all the character transitions
        before considering taking an action transition.  The priority
        allows that; transitions are checked in priority order, from
        lowest numerical value to highest.  Note that priority 0 is
        reserved for ``Epsilon`` transitions.
        """

        pass  # pragma: no cover


class Epsilon(Transition):
    """
    Represent epsilon transitions.  These transitions are an integral
    part of non-deterministic finite automata and are used for
    constructing the lexer.  This transition takes no arguments.
    """

    trans_args = set()
    priority = 0

    @classmethod
    def disjoint(cls, transitions):
        """
        Given a list of transitions, this class method must create a new
        list of disjoint transitions that will transition between the
        same set of states.  This implementation simply returns the
        input transitions list unchanged, as all epsilon transitions
        between two states are equivalent.

        :param list transitions: A list of ``Transition`` instances.

        :returns: An iterator that produces lists of disjoint
                  transitions.  Note that this is essentially a list
                  of lists, where each element of the inner list is a
                  ``Transition`` instance.
        """

        return [transitions]

    def match(self, char, sim):
        """
        Determine if the character is matched by this transition.  Used
        when simulating the automaton.  This implementation raises a
        ``TypeError``, as the simulator is not designed to simulate a
        non-deterministic finite automaton.

        :param str char: The character to match, or ``None`` at the
                         end of the string.
        :param sim: The simulator.  This may be used to access
                    simulation state information, such as the lexeme
                    being processed.
        :type sim: ``plexgen.simulator.Simulator``

        :returns: A ``True`` value if the transition was matched.
                  Note that it is the transition's responsibility to
                  call the ``sim.consume()`` method if the character
                  is to be consumed.
        :rtype: ``bool``
        """

        raise TypeError('cannot simulate a non-deterministic finite automaton')

    def merge(self, others):
        """
        Given a set of other transitions between the same two states,
        merge all the transitions (including this one) into the
        smallest possible set.  This implementation returns a set
        containing a single transition, as all epsilon transitions are
        equivalent.

        :param set others: A set of ``Transition`` instances with the
                           same priority.

        :returns: Either a new ``set`` containing merged
                  ``Transition`` instances, or ``None`` if merging is
                  not possible.
        """

        return set([self])


class MatchChar(Transition):
    """
    Represent character matching transitions.  These transitions
    consume characters from the input, making the transition only if
    the character is in the defined character set.  The sole required
    argument is the ``cset`` argument, which should be a
    ``plexgen.charset.CharSet``.
    """

    trans_args = set(['cset'])
    priority = 1

    @classmethod
    def disjoint(cls, transitions):
        """
        Given a list of transitions, this class method must create a new
        list of disjoint transitions that will transition between the
        same set of states.  This implementation uses the
        ``plexgen.charset.CharSet.disjoint()`` method to split the
        transitions into sets of non-overlapping transitions.

        :param list transitions: A list of ``Transition`` instances.

        :returns: An iterator that produces lists of disjoint
                  transitions.  Note that this is essentially a list
                  of lists, where each element of the inner list is a
                  ``Transition`` instance.
        """

        # Begin by producing a map from the character set to the
        # original transition
        cset_map = {id(t.cset): t for t in transitions}

        # Calculate the disjoint of all the character sets and build
        # the transition lists to produce
        for dj_cset, in_csets in charset.CharSet.disjoint(
                *(t.cset for t in transitions)):
            yield [
                cls(
                    cset_map[id(cs)].state_out,
                    cset_map[id(cs)].state_in,
                    cset=dj_cset,
                )
                for cs in in_csets
            ]

    def match(self, char, sim):
        """
        Determine if the character is matched by this transition.  Used
        when simulating the automaton.  This implementation consumes
        characters only if they match the character set of the
        transition.

        :param str char: The character to match, or ``None`` at the
                         end of the string.
        :param sim: The simulator.  This may be used to access
                    simulation state information, such as the lexeme
                    being processed.
        :type sim: ``plexgen.simulator.Simulator``

        :returns: A ``True`` value if the transition was matched.
                  Note that it is the transition's responsibility to
                  call the ``sim.consume()`` method if the character
                  is to be consumed.
        :rtype: ``bool``
        """

        # End of string?
        if char is None:
            return False

        if char in self.cset:
            # Matched, consume the character
            sim.consume()
            return True

        return False

    def merge(self, others):
        """
        Given a set of other transitions between the same two states,
        merge all the transitions (including this one) into the
        smallest possible set.  This implementation merges the
        character sets of all the transitions into this single
        transition.

        :param set others: A set of ``Transition`` instances with the
                           same priority.

        :returns: Either a new ``set`` containing merged
                  ``Transition`` instances, or ``None`` if merging is
                  not possible.
        """

        for other in others:
            self.cset |= other.cset

        return set([self])


class Action(Transition):
    """
    Represent action transitions.  These transitions are only used in
    the ``plexgen.automaton.Lexer`` automaton, and provide the core
    functionality of the lexer generator.

    This transition requires an ``action`` argument--containing the
    text of the action to take when executing the action--and a
    ``precedence`` argument--an integer indicating which action takes
    priority.  The ``precedence`` argument is important; in a lexer
    which recognizes, say, keywords as well as identifiers, the
    precedence ensures that keywords (entered with a numerically
    smaller precedence) will have their action taken instead of the
    identifier action (entered with a numerically higher precedence).
    The ``precedence`` parameter frequently comes from the line number
    of the input lexer specification.

    One optional parameter is provided: the ``name`` parameter can be
    used to provide a short name to associate with the action.  This
    might be useful in outputting the actual lexers.
    """

    trans_args = set(['action', 'precedence', 'name'])
    priority = 2
    defaults = {
        'name': None,
    }

    @classmethod
    def disjoint(cls, transitions):
        """
        Given a list of transitions, this class method must create a new
        list of disjoint transitions that will transition between the
        same set of states.  This implementation returns each
        transition as an independent list, as action transitions are
        never equivalent.

        :param list transitions: A list of ``Transition`` instances.

        :returns: An iterator that produces lists of disjoint
                  transitions.  Note that this is essentially a list
                  of lists, where each element of the inner list is a
                  ``Transition`` instance.
        """

        return [[t] for t in transitions]

    def match(self, char, sim):
        """
        Determine if the character is matched by this transition.  Used
        when simulating the automaton.  This implementation always
        matches, but does not consume the character.

        :param str char: The character to match, or ``None`` at the
                         end of the string.
        :param sim: The simulator.  This may be used to access
                    simulation state information, such as the lexeme
                    being processed.
        :type sim: ``plexgen.simulator.Simulator``

        :returns: A ``True`` value if the transition was matched.
                  Note that it is the transition's responsibility to
                  call the ``sim.consume()`` method if the character
                  is to be consumed.
        :rtype: ``bool``
        """

        # Extract the lexeme
        lexeme = sim.get_lexeme()

        # Prepare for the next lexeme
        sim.start_lexeme()

        # Trigger the action
        sim.action(self.name, self.action, lexeme)

        # Note: character is *not* consumed
        return True

    def merge(self, others):
        """
        Given a set of other transitions between the same two states,
        merge all the transitions (including this one) into the
        smallest possible set.  This implementation returns a set
        containing a single transition, the one with the smallest
        numerical precedence.

        :param set others: A set of ``Transition`` instances with the
                           same priority.

        :returns: Either a new ``set`` containing merged
                  ``Transition`` instances, or ``None`` if merging is
                  not possible.
        """

        # Add ourself to the set
        others.add(self)

        # Return the one with the smallest precedence
        return set([sorted(others, key=lambda x: x.precedence)[0]])
