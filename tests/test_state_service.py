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
from ..state_service.state_service import app


class TestStateService(TestCase):

    module = 'state_service.state_service.state_chart.StateChart'
    patched_chart_func = f'{module}._read_chart'

    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    def tearDown(self):
        self.app = None

    @mock.patch(patched_chart_func, return_value=chart_fixture())
    def test_get_state_tests_current_state(self, *patch):
        expected = 200
        actual = self.app.get('/state?state=state_1')

        self.assertEqual(expected, actual.status_code)

        expected = b'state_1'
        self.assertEqual(expected, actual.data)

    @mock.patch(patched_chart_func, return_value=chart_fixture())
    def test_put_state_updates_current_state(self, *patch):
        self.app.put('/state?state=state_1')

        expected = 200
        actual = self.app.get('/state?state=state_1')

        self.assertEqual(expected, actual.status_code)

        expected = b'state_1'
        self.assertEqual(expected, actual.data)

        self.app.put('/state?state=state_1')

        expected = 406
        self.app.put('/state?state=state_1')
        actual = self.app.get('/state?state=state_1')

        self.assertEqual(expected, actual.status_code)

        expected = 200
        actual = self.app.get('/state?state=state_2')

        self.assertEqual(expected, actual.status_code)

        expected = b'state_2'
        self.assertEqual(expected, actual.data)
