#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

import logging
import threading

from datetime import datetime
from enum import Enum


class Action(Enum):
    INCREMENT = 'increment'
    TIME = 'time'


class StateData(dict):
    """
    Represents a nested `dict` in a State.

    This is used to avoid using `State` to describe nested
    `dict`s, which would add the properties of State to
    nested states, e.g., `is_end_state`. These properties
    only have meaning when describing a `State` object.
    """

    def __init__(self, data):
        super(StateData, self).__init__(data)

        for key in self:
            value = self[key]
            if isinstance(value, list):
                for index, item in enumerate(value):
                    if isinstance(item, dict):
                        value[index] = StateData(item)

            elif isinstance(value, dict):
                self[key] = StateData(value)

    def __getattr__(self, key):
        return self[key]


class State(dict):
    """
    Represents a state, including when the state should transition to
    another state.

    A state transitions when its current 'state' meets criteria for entering
    a new 'state'. The criteria are stored in `current` and `target`
    attributes. Each of these values is characterized with a 'key' and a
    'value', so that a a comparison can be made. When the state is
    asynchronous, the `current` value is not used and instead the current
    (system) time is used.

    States transition by applying an action to the current state and checking
    if the current value equals the target value. The action is provided
    in the definition of the state. The action can be `increment`, which
    increments a value, or `time`, which schedules when a state transition
    will occur.

    A state that does not provide an action is determined to be the final or
    end state.

    State subclasses `dict` and overrides the `__init__` method to provide
    'dot' method accessors for the `dict`'s keys.
    """

    DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'

    def __init__(self, data):
        super(State, self).__init__(data)

        self._did_enter_state = False
        self._lock = threading.Lock()
        self._logger = None
        self._transition_time = None

        for key in self:
            value = self[key]
            if isinstance(value, list):
                for index, item in enumerate(value):
                    if isinstance(item, dict):
                        value[index] = State(item)

            elif isinstance(value, dict):
                self[key] = StateData(value)

    def increment(self):
        """
        Increments the current state's value and attempts to transition
        to the state's target state.
        """
        self.current.value += 1
        self.transition()

    def time(self):
        """
        Used by an asynchronous state to transition to its target
        state.
        """
        self.transition()

    def to_dict(self):
        """
        Represents the State instance as a `dict`.

        An asynchronous state does not have a `current` key and
        a normal state does. We deal with each case separately
        and avoid overriding `__getattr__` with exception handling.

        Returns:
            - A `dict` representing the latest state
        """
        if self.is_end_state:
            return {
                'name': self.name,
            }

        value = {
            'name': self.name,
            'func': self.action,
            'target': {
                'name': self.target.name,
                'when': {
                    'key': self.target.when.key,
                    'value': self.target.when.value,
                },
            },
        }

        if not self.is_async:
            value['current'] = {
                'key': self.current.key,
                'value': self.current.value,
            }

        return value

    def transition(self):
        """
        Transitions from the current state to the its target state.

        Returns:
            True if the transition was successful
            False otherwise
        """
        can_transition = self._can_transition()
        if can_transition:
            self._enter_state()

    def update(self):
        """
        Updates the state using the action defined by the user.

        Returns:
            True if the action was successful
            False otherwise
        """
        func = getattr(self, self.action)
        func()

    @property
    def action(self):
        """
        Returns the action to perform when updating the state.
        """
        return self.func

    @property
    def delegate(self):
        if self._delegate is None:
            raise RuntimeError(f'State {self.name} has no delegate')

        return self._delegate

    @delegate.setter
    def delegate(self, value):
        self._delegate = value

    @property
    def did_enter_state(self):
        return self._did_enter_state

    @property
    def is_async(self):
        return self.action == Action.TIME.value

    @property
    def is_end_state(self):
        """
        Returns if the state is the final or end state.

        For end states, no action is defined, so calling it
        will raise an error.
        """
        try:
            self.action
        except KeyError:
            return True

        return False

    @property
    def lock(self):
        return self._lock

    @property
    def logger(self):
        if self._logger is None:
            self._logger = logging.getLogger(self.__class__.__name__)

        return self._logger

    @property
    def transition_time(self):
        if self._transition_time is None:
            self._transition_time = datetime.strptime(
                self.target.when.value, State.DATE_FORMAT)

        return self._transition_time

    def _can_transition(self):
        """
        Decides if the state's current and target value meet the criterion
        for transitioning to the state's target state.

        Returns:

            For increment action, if the value associated with the
            current state equals the value associated with the target state.

            For time action, if the value associated with the current state
            is before the value associated with the target state.
        """

        if self.action == Action.INCREMENT.value:
            return self.current.value == self.target.when.value
        elif self.action == Action.TIME.value:
            now = self._now()
            then = self.transition_time
            return then < now

        return False

    def _enter_state(self):
        new_state_name = self.target.name

        self.lock.acquire()
        try:
            self._did_enter_state = self.delegate.did_enter_state(
                self, new_state_name)
        finally:
            self.lock.release()

    def _now(self):
        return datetime.now()

    def __getattr__(self, key):
        return self[key]
