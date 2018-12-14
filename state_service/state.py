#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

from datetime import datetime


class State:
    """
    Represents a state, including when the state should transition to
    another state.

    A state transitions when its current 'state' meets criteria for entering
    a new 'state'. The criteria are defined in a `dict`, 'current,' and
    'target'; each dict is defined by a 'key' and a 'value', so that a
    a comparison can be made.

    States transition by applying a function to the current state and checking
    if the current state equals the target state. The function is provided
    in the definition of the state. The function can be `increment`, which
    increments a value, or `time`, which schedules when a state transition
    will occur.

    A state that does not provide a function is determined to be the last or
    end state.
    """

    DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'

    INCREMENT_FUNC = 'increment'
    TIME_FUNC = 'time'


    def __init__(self, definition):
        self._name = None
        self._function = None
        self._target_name = ''
        self._current_state = {
            'key': '',
            'value': '',
        }
        self._target_state = {}
        self._delegate = None
        self._did_enter_state = False
        self._is_end_state = False

        self._define(definition)

    def to_dict(self):
        if self.is_end_state:
            return {
                'name': self.name,
            }

        target_value = self._target_value()
        return {
            'name': self.name,
            'func': self.function,
            'current': {
                'key': self.current_state['key'],
                'value': self.current_state['value']
            },
            'target': {
                'name': self.target_name,
                'when': {
                    'key': self.target_state['key'],
                    'value': target_value,
                },
            },
        }

    def transition(self):
        can_transition = self._can_transition()
        if can_transition:
            self._enter_state()

        return self._did_enter_state

    def update(self):
        func = getattr(self, self.function)
        func()
        self.delegate.save()

    def time(self):
        if not self.transition():
            raise RuntimeError(f'Failed to update {self.name} state')

    def increment(self):
        self.current_state['value'] += 1
        self.transition()

    @property
    def did_enter_state(self):
        return self._did_enter_state

    @property
    def function(self):
        return self._function

    @property
    def is_end_state(self):
        return self._is_end_state

    @property
    def name(self):
        return self._name

    @property
    def current_state(self):
        return self._current_state

    @property
    def delegate(self):
        return self._delegate

    @delegate.setter
    def delegate(self, value):
        self._delegate = value

    @property
    def target_name(self):
        return self._target_name

    @property
    def target_state(self):
        return self._target_state

    def _can_transition(self):
        """
        For increment functions:

            Returns if the value associated with the current state equals the
            value associated with the target state.

        For time functions:

            Returns if the value associated with the current state is before
            the value associated with the target state.
        """

        if self.function == State.TIME_FUNC:
            now = self._now()
            target = self.target_state['value']
            return target < now
        elif self.function == State.INCREMENT_FUNC:
            current_value = self.current_state['value']
            target_value = self.target_state['value']
            return current_value == target_value

        return False

    def _define(self, definition):
        self._name = definition['name']
        try:
            self._function = definition['func']
        except KeyError:
            self._is_end_state = True
            return

        try:
            current = definition['current']
        except KeyError as e:
            # current is defined as a default
            pass
        else:
            self._define_now(current)

        target = definition['target']
        self._define_target(target)

    def _define_now(self, value):
        self._current_state = value

    def _define_target(self, value):
        self._target_name = value['name']
        self._target_state = value['when']
        if self.function == State.TIME_FUNC:
            self._target_state['value'] = datetime.strptime(
                value['when']['value'], State.DATE_FORMAT
            )

    def _enter_state(self):
        new_state_name = self.target_name
        self._did_enter_state = self.delegate.did_enter_state(
            self, new_state_name)

    def _now(self):
        return datetime.now()

    def _target_value(self):
        value = self.target_state['value']
        if self.function == State.TIME_FUNC:
            return value.strftime(State.DATE_FORMAT)

        return value
