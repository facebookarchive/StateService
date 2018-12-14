#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

from unittest import mock
from unittest import TestCase

from datetime import datetime

from .test_fixtures import state_machine_fixture
from .test_fixtures import time_machine_fixture
from ..state_service.state_machine import StateMachine


class TestStateMachine(TestCase):

    machine_module = 'state_service.state_service.state_machine.StateMachine'
    state_module = 'state_service.state_service.state.State'
    patched_machine_func = f'{machine_module}._read_machine'
    patched_save_func = f'{machine_module}.save'
    patched_now_func = f'{state_module}._now'

    def setUp(self):
        self.machine = StateMachine('/tmp/machine.yaml')

    def tearDown(self):
        self.machine = None

    @mock.patch(patched_machine_func, return_value=state_machine_fixture())
    def test_normal_state_machine_initializes_correctly(self, *patch):
        expected = 3
        actual = len(self.machine.states)

        self.assertEqual(expected, actual)

    @mock.patch(patched_machine_func, return_value=state_machine_fixture())
    @mock.patch(patched_save_func, return_value=True)
    def test_normal_state_machine_records_transition(self, *patch):
        current_state = self.machine.current_state
        expected = 'state_1'
        actual = current_state.name

        self.assertEqual(expected, actual)

        current_state.update()
        current_state = self.machine.current_state
        actual = current_state.name

        self.assertEqual(expected, actual)

        current_state.update()
        current_state = self.machine.current_state
        expected = 'state_2'
        actual = current_state.name

        self.assertEqual(expected, actual)

    @mock.patch(patched_machine_func, return_value=time_machine_fixture())
    def test_time_state_machine_initializes_correctly(self, *patch):
        expected = 3
        actual = len(self.machine.states)

        self.assertEqual(expected, actual)

    @mock.patch(patched_machine_func, return_value=time_machine_fixture())
    @mock.patch(patched_save_func, return_value=True)
    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 3, 0))
    def test_time_state_machine_records_transition(self, *patch):
        current_state = self.machine.current_state
        expected = 'state_1'
        actual = current_state.name

        self.assertEqual(expected, actual)

        current_state.update()
        current_state = self.machine.current_state
        expected = 'state_2'
        actual = current_state.name

        self.assertEqual(expected, actual)
