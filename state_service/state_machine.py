#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

import os
import json
import pickle
import threading
import yaml

from datetime import datetime

from .state import State
from .state_delegate import StateDelegate

#
# Import all ML libraries that the _deserialize_model method will
# require.
#
# One file (ml_modules.py) is used to list all models, so that
# edits to the main codebase are minimized and duplicate imports
# are avoided.
#
from .ml_modules import *  # noqa: F401,F403


class StateMachine(StateDelegate):
    """
    Represents a state machine, including all its states, and the current
    active state.

    When configured with an explicit state machine, StateMachine updates
    the current state. When the explicit state machine is asynchronous
    (scheduled), StateMachine stops and starts a `threaded.Timer` instance
    to schedule updating the current state. StateMachine also persists the
    state machine to file storage after every update.

    When configured as an implicit state machine, StateMachine predicts the
    state of an application or machine using ML models that it hosts.
    """

    def __init__(self, options):
        self._current_state = None
        self._current_state_name = None
        self._machine = None
        self._models = None
        self._options = options
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

    def predict(self, model_name, values):
        """
        Predicts the state of a machine using a hosted model.

        Args:
            model_name (str): Name of a model to deserialize
            values (list): Values that will be used as inputs to the model

        Returns:
            list: The predicted state of the machine
        """
        conf = self.models[model_name]
        team, model = conf['team'], conf['model']
        deserialized_model = self._deserialize_model(team, model)

        if deserialized_model is None:
            raise RuntimeError(f'No model is available for {team}/{model}.pkl')

        prediction = deserialized_model.predict(values)
        return [conf['states'][i] for i in prediction]

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
    def models(self):
        if self._models is None:
            self._models = {}

            conf_files = []
            for f in os.listdir(self._config_path()):
                name, ext = os.path.splitext(f)
                if ext.lower() == 'json':
                    conf_files.append(f)

            for conf_file in conf_files:
                filepath = os.path.join(
                    self._config_path(), conf_file
                )
                with open(filepath, 'r') as f:
                    try:
                        conf = json.load(f)
                        name = conf['name']
                        self._models[name] = conf
                    except KeyError:
                        raise RuntimeError(
                            f'{filepath} is missing :name key'
                        )
                    except ValueError:
                        raise RuntimeError(
                            f'{filepath} is not proper JSON'
                        )

        return self._models

    @property
    def states(self):
        return self._states

    def did_enter_state(self, old_state, new_state_name):
        """StateDelegate method"""
        self.states[old_state.name] = old_state
        self._current_state_name = new_state_name
        return True

    def _config_path(self):
        try:
            return self._options.config
        except AttributeError:
            raise RuntimeError('No configuration directory provided.')

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

    def _deserialize_model(self, team, model):
        model_path = os.path.join(
            self._models_path(), team, model
        )

        if os.path.exists(model_path):
            with open(model_path, 'rb') as serialized_model:
                try:
                    return pickle.load(serialized_model)
                except Exception:
                    raise RuntimeError(f'Unable to deserialize {model_path}')
        else:
            raise FileNotFoundError(f'{model_path} does not exist')

    def _machine_path(self):
        try:
            return self._options.machine
        except AttributeError:
            raise RuntimeError('No state machine provided.')

    def _models_path(self):
        try:
            return self._options.models
        except AttributeError:
            raise RuntimeError('No models directory provided.')

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

        machine_path = self._machine_path()

        if os.path.exists(machine_path):
            with open(machine_path, 'rt') as data:
                try:
                    return yaml.load(data)
                except yaml.YAMLError:
                    raise RuntimeError(f'{machine_path} is not a YAML file')
        else:
            raise FileNotFoundError(f'{machine_path} does not exist')

    def _write_machine(self, data):
        """
        Writes the state machine to a YAML file.
        """

        machine_path = self._machine_path()

        with open(machine_path, 'wt') as f:
            yaml.dump(data, f, default_flow_style=False)
