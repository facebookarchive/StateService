#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

from collections import defaultdict

import os
import yaml

from .state import State
from .state_delegate import StateDelegate


def dict_constructor(loader, node):
        return defaultdict(str, loader.construct_pairs(node))


class StateMachine(StateDelegate):
    """
    Describes the states available, as well as identifying the current
    state.

    StateMachine acts as a delegate for State objects, so that the current
    state can be updated and the current state machine can be persisted after
    each update.
    """

    def __init__(self, path):
        self._machine = None
        self._current_state = None
        self._current_state_name = ''
        self._path = path
        self._states = None

    def did_enter_state(self, old_state, new_state_name):
        """StateDelegate method"""
        old_state_name = old_state.name
        self.states[old_state_name] = old_state
        self._current_state_name = new_state_name
        return True

    def save(self):
        """StateDelegate method"""
        states_as_dict = [state.to_dict() for state in list(self.states.values())]
        data = {
            'current_state': self._current_state_name,
            'states': states_as_dict,
        }
        with open(self.path, 'wt') as f:
            yaml.dump(data, f, default_flow_style=False)

    @property
    def machine(self):
        if self._machine is None:
            self._machine = self._read_machine()

        return self._machine

    @property
    def current_state(self):
        return self.states[self._current_state_name]

    @property
    def path(self):
        return self._path

    @property
    def states(self):
        if self._states is None:
            self._states = {}
            self._current_state_name = self.machine['current_state']
            self._define(self.machine['states'])

        return self._states

    def _define(self, definitions):
        for _, definition in enumerate(definitions):
            state = State(definition)
            state.delegate = self
            state_name = state.name
            self._states[state_name] = state

    def _read_machine(self):
        """
        Reads the state machine from a YAML file.

        Returns:
            - State machine (dict) if read from file
            - State machine (dict) that is only an end state, if path or file
            is missing

        Raises:
            - RuntimeError if YAML if not properly formatted
        """

        if self.path is None:
            return {
                'name': 'no_state',
            }

        if os.path.exists(self.path):
            with open(self.path, 'rt') as data:
                try:
                    machine = yaml.load(data)
                except yaml.YAMLError:
                    raise RuntimeError(f'{self.path} is not a YAML file')

            return machine
        else:
            return {
                'name': 'no_state',
            }
