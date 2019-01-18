#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

import os
import threading
import yaml

from datetime import datetime

from .state import State
from .state_delegate import StateDelegate


class StateMachine(StateDelegate):
    """
    Represents a state machine, including all its states, and the current
    active state.

    StateMachine is used to update the current state. When the state machine
    is asynchronous (scheduled), StateMachine stops and starts a
    `threaded.Timer` instance to schedule updating the current state.
    StateMachine also persists the state machine to file storage after
    every update.

    StateMachine acts as a delegate for State objects, so that the current
    state can be updated.
    """

    def __init__(self, path):
        self._current_state = None
        self._current_state_name = None
        self._machine = None
        self._path = path
        self._states = None
        self._thread_state = None

    def build(self):
        """
        Transforms a state machine in YAML format to a list of
        State objects and identifies the name of the current state.

        If the state machine is asynchronous, the state machine
        begins waiting for the current state to transition.
        """
        if self._machine is None:
            self._machine = self._read_machine()
            self._states = {}
            self._current_state_name = self.machine['current_state']
            self._states = self._create(self.machine['states'])

            if self.is_async:
                self._start_timer()

    def is_current_state(self, name):
        return self._current_state_name == name

    def save(self):
        states_as_dict = [state.to_dict() for state in list(self.states.values())]
        data = {
            'current_state': self._current_state_name,
            'states': states_as_dict,
        }

        self._write_machine(data)

    def update(self):
        """
        Requests the current state to update.

        The current state will update to its next state only if
        its condition for transitioning to that next state is
        true.

        Returns:
            - True if the update was successfuli, i.e., the state
              transitioned to its target state
            - False otherwise
        """
        if self.current_state.update():
            self.save()

            if not self.did_end and self.is_async:
                self._start_timer()

            return True

        return False

    @property
    def current_state(self):
        return self.states[self._current_state_name]

    @property
    def did_end(self):
        return self.current_state.is_end_state

    @property
    def is_async(self):
        return self.current_state.is_async

    @property
    def machine(self):
        return self._machine

    @property
    def states(self):
        return self._states

    def did_enter_state(self, old_state, new_state_name):
        """StateDelegate method"""
        old_state_name = old_state.name
        self.states[old_state_name] = old_state
        self._current_state_name = new_state_name
        return True

    def _create(self, states):
        result = {}
        for _, s in enumerate(states):
            state = State(s)
            state.delegate = self
            state_name = state.name
            result[state_name] = state

        return result

    def _current_state(self):
        return self.states[self._current_state_name]

    def _start_timer(self):
        if self._thread_state:
            self._thread_state.cancel()

        time = self.current_state.transition_time
        now = datetime.now()
        interval = (time - now).total_seconds()
        self._thread_state = threading.Timer(interval, self.update)
        self._thread_state.start()

    def _read_machine(self):
        """
        Reads the state machine from a YAML file.

        Returns:
            - State machine (dict) if read from file

        Raises:
            - FileNotFoundError if YAML file does not exist
            - RuntimeError if YAML if not properly formatted
        """

        if os.path.exists(self._path):
            with open(self._path, 'rt') as data:
                try:
                    machine = yaml.load(data)
                except yaml.YAMLError:
                    raise RuntimeError(f'{self._path} is not a YAML file')

            return machine
        else:
            raise FileNotFoundError(f'{self._path} does not exist')

    def _write_machine(self, data):
        """
        Writes the state machine to a YAML file.
        """

        with open(self._path, 'wt') as f:
            yaml.dump(data, f, default_flow_style=False)
