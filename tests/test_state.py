#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

from unittest import TestCase

from .test_fixtures import state_fixture
from ..state_service.state import State
from ..state_service.state_delegate import StateDelegate


class StateDelegateMock(StateDelegate):

    def did_enter_state(self, old_state, new_state):
        return True

    def save(self):
        pass


class TestState(TestCase):

    def setUp(self):
        self.state = State(state_fixture())
        self.state.delegate = StateDelegateMock()

    def tearDown(self):
        self.state = None

    def test_state_initializes_correctly(self):
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
        actual = self.state.did_enter_state
        self.assertFalse(actual)

    def test_can_transition_is_false_when_state_cannot_transition(self):
        actual = self.state._can_transition()
        self.assertFalse(actual)

    def test_can_transition_is_true_when_state_can_transition(self):
        self.state.current_state['value'] = self.state.target_state['value']
        actual = self.state._can_transition()
        self.assertTrue(actual)

    def test_transition_returns_false_if_state_cannot_transition(self):
        actual = self.state.transition()
        self.assertFalse(actual)

        actual = self.state.did_enter_state
        self.assertFalse(actual)

    def test_transition_returns_true_if_state_can_transition(self):
        self.state.current_state['value'] = self.state.target_state['value']
        actual = self.state.transition()
        self.assertTrue(actual)

        actual = self.state.did_enter_state
        self.assertTrue(actual)

    def test_update_transitions_to_new_state_correctly(self):
        actual = self.state.did_enter_state
        self.assertFalse(actual)

        self.state.update()
        actual = self.state.did_enter_state
        self.assertFalse(actual)

        self.state.update()
        actual = self.state.did_enter_state
        self.assertTrue(actual)
