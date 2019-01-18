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

from .test_fixtures import normal_state_fixture
from .test_fixtures import async_state_fixture
from ..state_service.state import State
from ..state_service.state_delegate import StateDelegate


class StateDelegateMock(StateDelegate):

    def did_enter_state(self, old_state, new_state):
        return True


class TestState(TestCase):

    delegate_module = 'state_service.tests.test_state.StateDelegateMock'
    state_module = 'state_service.state_service.state.State'
    patched_now_func = f'{state_module}._now'

    def setUp(self):
        pass

    def tearDown(self):
        self.state = None

    def set_up_normal_state_fixture(self):
        self.state = State(normal_state_fixture())
        self.state.delegate = StateDelegateMock()

    def set_up_async_state_fixture(self):
        self.state = State(async_state_fixture())
        self.state.delegate = StateDelegateMock()

    #
    # Testing normal states
    #
    def test_normal_state_initializes_correctly(self):
        self.set_up_normal_state_fixture()

        expected = 'state_1'
        actual = self.state.name

        self.assertEqual(expected, actual)

        expected = 'increment'
        actual = self.state.action

        self.assertEqual(expected, actual)

        expected = {
            'key': 'count',
            'value': 0,
        }
        actual = self.state.current

        self.assertEqual(expected, actual)

        expected = 'state_2'
        actual = self.state.target.name

        self.assertEqual(expected, actual)

        expected = {
            'key': 'count',
            'value': 2,
        }
        actual = self.state.target.when

        self.assertEqual(expected, actual)

    def test_normal_did_enter_state_is_initially_false(self):
        self.set_up_normal_state_fixture()

        actual = self.state.did_enter_state
        self.assertFalse(actual)

    def test_to_dict_records_a_normal_state_as_a_dict(self):
        self.set_up_normal_state_fixture()

        actual = self.state.to_dict()
        expected = normal_state_fixture()

        self.assertEqual(expected, actual)

    def test_can_transition_is_false_when_normal_state_cannot_transition(self):
        self.set_up_normal_state_fixture()

        actual = self.state._can_transition()
        self.assertFalse(actual)

    def test_can_transition_is_true_when_normal_state_can_transition(self):
        self.set_up_normal_state_fixture()

        self.state.current.value = self.state.target.when.value
        actual = self.state._can_transition()
        self.assertTrue(actual)

    def test_transition_returns_false_if_normal_state_cannot_transition(self):
        self.set_up_normal_state_fixture()

        actual = self.state.transition()
        self.assertFalse(actual)

        actual = self.state.did_enter_state
        self.assertFalse(actual)

    def test_transition_returns_true_if_normal_state_can_transition(self):
        self.set_up_normal_state_fixture()

        self.state.current.value = self.state.target.when.value
        actual = self.state.transition()
        self.assertTrue(actual)

        actual = self.state.did_enter_state
        self.assertTrue(actual)

    def test_update_transitions_to_new_normal_state_correctly(self):
        self.set_up_normal_state_fixture()

        actual = self.state.did_enter_state
        self.assertFalse(actual)

        self.state.update()
        actual = self.state.did_enter_state
        self.assertFalse(actual)

        self.state.update()
        actual = self.state.did_enter_state
        self.assertTrue(actual)

    #
    # Testing async states
    #
    def test_async_state_initializes_correctly(self):
        self.set_up_async_state_fixture()

        expected = 'state_1'
        actual = self.state.name

        self.assertEqual(expected, actual)

        expected = 'time'
        actual = self.state.action

        self.assertEqual(expected, actual)

        actual = self.state.is_async
        self.assertTrue(actual)

        with self.assertRaises(KeyError):
            self.state.current


        expected = 'state_2'
        actual = self.state.target.name

        self.assertEqual(expected, actual)

        expected = {
            'key': 'clock',
            'value': '3000-01-01T02:00:10',
        }
        actual = self.state.target.when

        self.assertEqual(expected, actual)

    def test_async_did_enter_state_is_initially_false(self):
        self.set_up_async_state_fixture()

        actual = self.state.did_enter_state
        self.assertFalse(actual)

    def test_to_dict_records_an_async_state_as_a_dict(self):
        self.set_up_async_state_fixture()

        actual = self.state.to_dict()
        expected = async_state_fixture()

        self.assertEqual(expected, actual)

    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 1, 0))
    def test_can_transition_is_false_when_async_state_cannot_transition(
        self, *patch
    ):
        self.set_up_async_state_fixture()

        actual = self.state._can_transition()
        self.assertFalse(actual)

    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 3, 0))
    def test_can_transition_is_true_when_async_state_can_transition(
        self, *patch
    ):
        self.set_up_async_state_fixture()

        actual = self.state._can_transition()
        self.assertTrue(actual)

    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 1, 0))
    def test_transition_returns_false_if_async_state_cannot_transition(
        self, *patch
    ):
        self.set_up_async_state_fixture()

        actual = self.state.transition()
        self.assertFalse(actual)

        actual = self.state.did_enter_state
        self.assertFalse(actual)

    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 3, 0))
    def test_transition_returns_true_if_async_state_can_transition(self, *patch):
        self.set_up_async_state_fixture()

        actual = self.state.transition()
        self.assertTrue(actual)

        actual = self.state.did_enter_state
        self.assertTrue(actual)

    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 3, 0))
    def test_update_transitions_to_new_async_state_correctly(self, *patch):
        self.set_up_async_state_fixture()

        actual = self.state.did_enter_state
        self.assertFalse(actual)

        self.state.update()
        actual = self.state.did_enter_state
        self.assertTrue(actual)
