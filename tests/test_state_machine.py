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

from .test_fixtures import normal_machine_fixture
from .test_fixtures import async_machine_fixture
from ..state_service.state_machine import StateMachine


class TestStateMachine(TestCase):

    machine_module = 'state_service.state_service.state_machine.StateMachine'
    state_module = 'state_service.state_service.state.State'
    patched_machine_func = f'{machine_module}._read_machine'
    patched_now_func = f'{state_module}._now'
    patched_save_func = f'{machine_module}.save'

    @mock.patch(patched_save_func, return_value=True)
    def setUp(self, *patch):
        self.machine = StateMachine('/tmp/machine.yml')

    def tearDown(self):
        self.machine = None

    def test_read_machine_raises_filenotfound_error_without_path(self):
        with self.assertRaises(FileNotFoundError):
            self.machine.build()

    @mock.patch(patched_machine_func, return_value=normal_machine_fixture())
    def test_state_machine_does_not_call_save_unless_update(self, *patch):
        self.machine.build()

        with mock.patch(TestStateMachine.patched_save_func) as mock_save:
            self.machine.update()
            mock_save.assert_not_called()

    @mock.patch(patched_machine_func, return_value=normal_machine_fixture())
    def test_state_machine_calls_save_if_update(self, *patch):
        self.machine.build()
        self.machine.update()

        with mock.patch(TestStateMachine.patched_save_func) as mock_save:
            self.machine.update()
            mock_save.assert_called_once()

    @mock.patch(patched_machine_func, return_value=normal_machine_fixture())
    def test_normal_state_machine_initializes_correctly(self, *patch):
        self.machine.build()

        expected = 3
        actual = len(self.machine.states)

        self.assertEqual(expected, actual)

        actual = self.machine.is_async
        self.assertFalse(actual)

    @mock.patch(patched_machine_func, return_value=normal_machine_fixture())
    @mock.patch(patched_save_func, return_value=True)
    def test_normal_state_machine_records_transition(self, *patch):
        self.machine.build()

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

    @mock.patch(patched_machine_func, return_value=normal_machine_fixture())
    @mock.patch(patched_save_func, return_value=True)
    def test_normal_state_machine_recognizes_end_state(self, *patch):
        self.machine.build()

        current_state = self.machine.current_state
        expected = 'state_1'
        actual = current_state.name

        self.assertEqual(expected, actual)

        current_state.update()
        current_state = self.machine.current_state
        current_state.update()
        current_state = self.machine.current_state
        current_state.update()
        current_state = self.machine.current_state

        current_state = self.machine.current_state
        expected = 'state_3'
        actual = current_state.name

        self.assertEqual(expected, actual)

        actual = self.machine.did_end

        self.assertTrue(actual)

    @mock.patch(patched_machine_func, return_value=async_machine_fixture())
    def test_async_state_machine_initializes_correctly(self, *patch):
        self.machine.build()

        expected = 3
        actual = len(self.machine.states)

        self.assertEqual(expected, actual)

        actual = self.machine.is_async
        self.assertTrue(actual)

    @mock.patch(patched_machine_func, return_value=async_machine_fixture())
    @mock.patch(patched_save_func, return_value=True)
    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 3, 0))
    def test_async_state_machine_records_transition(self, *patch):
        self.machine.build()

        current_state = self.machine.current_state
        expected = 'state_1'
        actual = current_state.name

        self.assertEqual(expected, actual)

        current_state.update()
        current_state = self.machine.current_state
        expected = 'state_2'
        actual = current_state.name

        self.assertEqual(expected, actual)
