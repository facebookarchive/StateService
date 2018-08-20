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

from .test_fixtures import chart_fixture
from ..state_service.state_chart import StateChart


class TestStateChart(TestCase):

    module = 'state_service.state_service.state_chart.StateChart'
    patched_chart_func = f'{module}._read_chart'
    patched_save_func = f'{module}.save'

    def setUp(self):
        self.chart = StateChart('/tmp/chart.yaml')

    def tearDown(self):
        self.chart = None

    @mock.patch(patched_chart_func, return_value=chart_fixture())
    def test_state_chart_initializes_correctly(self, *patch):
        expected = 3
        actual = len(self.chart.states)

        self.assertEqual(expected, actual)

    @mock.patch(patched_chart_func, return_value=chart_fixture())
    @mock.patch(patched_save_func, return_value=True)
    def test_state_chart_records_transition(self, *patch):
        current_state = self.chart.current_state
        expected = 'state_1'
        actual = current_state.name

        self.assertEqual(expected, actual)

        current_state.update()
        current_state = self.chart.current_state
        actual = current_state.name

        self.assertEqual(expected, actual)

        current_state.update()
        current_state = self.chart.current_state
        expected = 'state_2'
        actual = current_state.name

        self.assertEqual(expected, actual)
