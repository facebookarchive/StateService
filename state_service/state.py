#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#


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
    in the definition of the state; presently, the only function that is
    supported is 'increment.'

    A state that does not provide a function is determined to be the last or
    end state.
    """

    def __init__(self, definition):
        self._name = None
        self._function = None
        self._target_name = ''
        self._current_state = None
        self._target_state = None
        self._delegate = None
        self._did_enter_state = False
        self._is_end_state = False

        self._define(definition)

    def to_dict(self):
        if self.is_end_state:
            return {
                'name': self.name,
            }

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
                    'value': self.target_state['value'],
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
        try:
            func()
        except Exception:
            raise RuntimeError(f'Failed to update {self.name} state')
        else:
            self.delegate.save()

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
        Returns if the value associated with the current state equals the
        value associated with the target state.
        """
        if self.current_state is None:
            return False

        current_value = self.current_state['value']
        target_value = self.target_state['value']

        return current_value == target_value

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
            raise e
        else:
            self._define_now(current)

        try:
            target = definition['target']
        except KeyError as e:
            raise e
        else:
            self._define_target(target)

    def _define_now(self, value):
        self._current_state = value

    def _define_target(self, value):
        self._target_name = value['name']
        self._target_state = value['when']

    def _enter_state(self):
        new_state_name = self.target_name
        self._did_enter_state = self.delegate.did_enter_state(
            self, new_state_name)
