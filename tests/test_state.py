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

from .test_fixtures import simple_state_fixture
from .test_fixtures import time_state_fixture
from ..state_service.state import State
from ..state_service.state_delegate import StateDelegate


class StateDelegateMock(StateDelegate):

    def did_enter_state(self, old_state, new_state):
        return True

    def save(self):
        pass


class TestState(TestCase):

    state_module = 'state_service.state_service.state.State'
    patched_now_func = f'{state_module}._now'

    def setUp(self):
        pass

    def tearDown(self):
        self.state = None

    def set_up_simple_state_fixture(self):
        self.state = State(simple_state_fixture())
        self.state.delegate = StateDelegateMock()

    def set_up_time_state_fixture(self):
        self.state = State(time_state_fixture())
        self.state.delegate = StateDelegateMock()

    def test_simple_state_initializes_correctly(self):
        self.set_up_simple_state_fixture()

        expected = 'state_1'
        actual = self.state.name

        self.assertEqual(expected, actual)

        expected = 'increment'
        actual = self.state.function

        self.assertEqual(expected, actual)

        expected = {
            'key': 'count',
            'value': 0,
        }
        actual = self.state.current_state

        self.assertEqual(expected, actual)

        expected = 'state_2'
        actual = self.state.target_name

        self.assertEqual(expected, actual)

        expected = {
            'key': 'count',
            'value': 2,
        }
        actual = self.state.target_state

        self.assertEqual(expected, actual)

    def test_did_enter_state_is_initially_false(self):
        self.set_up_simple_state_fixture()

        actual = self.state.did_enter_state
        self.assertFalse(actual)

    def test_can_transition_is_false_when_simple_state_cannot_transition(self):
        self.set_up_simple_state_fixture()

        actual = self.state._can_transition()
        self.assertFalse(actual)

    def test_can_transition_is_true_when_simple_state_can_transition(self):
        self.set_up_simple_state_fixture()

        self.state.current_state['value'] = self.state.target_state['value']
        actual = self.state._can_transition()
        self.assertTrue(actual)

    def test_transition_returns_false_if_simple_state_cannot_transition(self):
        self.set_up_simple_state_fixture()

        actual = self.state.transition()
        self.assertFalse(actual)

        actual = self.state.did_enter_state
        self.assertFalse(actual)

    def test_transition_returns_true_if_simple_state_can_transition(self):
        self.set_up_simple_state_fixture()

        self.state.current_state['value'] = self.state.target_state['value']
        actual = self.state.transition()
        self.assertTrue(actual)

        actual = self.state.did_enter_state
        self.assertTrue(actual)

    def test_update_transitions_to_new_simple_state_correctly(self):
        self.set_up_simple_state_fixture()

        actual = self.state.did_enter_state
        self.assertFalse(actual)

        self.state.update()
        actual = self.state.did_enter_state
        self.assertFalse(actual)

        self.state.update()
        actual = self.state.did_enter_state
        self.assertTrue(actual)

    def test_time_state_initializes_correctly(self):
        self.set_up_time_state_fixture()

        expected = 'state_1'
        actual = self.state.name

        self.assertEqual(expected, actual)

        expected = 'time'
        actual = self.state.function

        self.assertEqual(expected, actual)

        expected = {
            'key': '',
            'value': '',
        }
        actual = self.state.current_state

        self.assertEqual(expected, actual)

        expected = 'state_2'
        actual = self.state.target_name

        self.assertEqual(expected, actual)

        expected = {
            'key': 'clock',
            'value': datetime(3000, 1, 1, 2, 0, 10),
        }
        actual = self.state.target_state

        self.assertEqual(expected, actual)

    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 1, 0))
    def test_can_transition_is_false_when_time_state_cannot_transition(self, *patch):
        self.set_up_time_state_fixture()

        actual = self.state._can_transition()
        self.assertFalse(actual)

    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 3, 0))
    def test_can_transition_is_true_when_time_state_can_transition(self, *patch):
        self.set_up_time_state_fixture()

        actual = self.state._can_transition()
        self.assertTrue(actual)

    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 1, 0))
    def test_transition_returns_false_if_time_state_cannot_transition(self, *patch):
        self.set_up_time_state_fixture()

        actual = self.state.transition()
        self.assertFalse(actual)

        actual = self.state.did_enter_state
        self.assertFalse(actual)

    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 3, 0))
    def test_transition_returns_true_if_time_state_can_transition(self, *patch):
        self.set_up_time_state_fixture()

        actual = self.state.transition()
        self.assertTrue(actual)

        actual = self.state.did_enter_state
        self.assertTrue(actual)

    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 1, 0))
    def test_transition_raises_error_if_time_state_is_early(self, *patch):
        self.set_up_time_state_fixture()

        self.assertRaises(RuntimeError, self.state.time)

    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 3, 0))
    def test_update_transitions_to_new_time_state_correctly(self, *patch):
        self.set_up_time_state_fixture()

        actual = self.state.did_enter_state
        self.assertFalse(actual)

        self.state.update()
        actual = self.state.did_enter_state
        self.assertTrue(actual)
