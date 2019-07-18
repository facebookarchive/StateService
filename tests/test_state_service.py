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

from .test_fixtures import argparse_fixture
from .test_fixtures import async_machine_fixture
from .test_fixtures import normal_machine_fixture
from .test_fixtures import predict_fixture
from ..state_service.state_service import app
from ..state_service.state_service import state_service


class TestStateService(TestCase):

    machine_module = 'state_service.state_service.state_machine.StateMachine'
    parser_module = 'argparse.ArgumentParser'
    state_module = 'state_service.state_service.state.State'
    patched_models_func = f'{machine_module}.models'
    patched_now_func = f'{state_module}._now'
    patched_parser_func = f'{parser_module}.parse_known_args'
    patched_predict_func = f'{machine_module}.predict'
    patched_read_machine_func = f'{machine_module}._read_machine'
    patched_save_func = f'{machine_module}.save'
    patched_write_machine_func = f'{machine_module}._write_machine'

    def setUp(self, *patch):
        app.testing = True
        self.app = app.test_client()

    def tearDown(self):
        self.app = None
        state_service._machine = None

    @mock.patch(patched_parser_func, return_value=argparse_fixture())
    @mock.patch(patched_read_machine_func, return_value=normal_machine_fixture())
    def test_get_normal_state_tests_current_state(self, *patch):
        state_service._initialize()

        expected = 200
        actual = self.app.get('/state?state=state_1')

        self.assertEqual(expected, actual.status_code)

        expected = b'state_1'
        self.assertEqual(expected, actual.data)

    @mock.patch(patched_parser_func, return_value=argparse_fixture())
    @mock.patch(patched_read_machine_func, return_value=normal_machine_fixture())
    @mock.patch(patched_write_machine_func, return_value=None)
    def test_put_normal_state_updates_current_state(self, *patch):
        state_service._initialize()

        expected = 200
        actual = self.app.get('/state?state=state_1')

        self.assertEqual(expected, actual.status_code)

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

    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 3, 0))
    @mock.patch(patched_parser_func, return_value=argparse_fixture())
    @mock.patch(patched_read_machine_func, return_value=async_machine_fixture())
    def test_get_async_state_tests_current_state(self, *patch):
        state_service._initialize()

        expected = 200
        actual = self.app.get('/state?state=state_1')

        self.assertEqual(expected, actual.status_code)

        expected = b'state_1'
        self.assertEqual(expected, actual.data)

    @mock.patch(patched_now_func, return_value=datetime(3000, 1, 1, 3, 0))
    @mock.patch(patched_parser_func, return_value=argparse_fixture())
    @mock.patch(patched_read_machine_func, return_value=async_machine_fixture())
    @mock.patch(patched_save_func, return_value=True)
    @mock.patch(patched_write_machine_func, return_value=None)
    def test_put_async_state_returns_406(self, *patch):
        state_service._initialize()

        expected = 200
        actual = self.app.get('/state?state=state_1')

        self.assertEqual(expected, actual.status_code)

        expected = 500
        actual = self.app.put('/state?state=state_1')

        self.assertEqual(expected, actual.status_code)

    @mock.patch(patched_predict_func, return_value=predict_fixture())
    @mock.patch(patched_read_machine_func, return_value=normal_machine_fixture())
    def test_post_state_returns_predicted_state(self, *patch):
        data = {
            'name': 'fixture',
            'values': [100, 0],
        }
        expected = ['run']
        actual = self.app.post('/state', json=data)

        self.assertEqual(expected, actual.json['state'])

    @mock.patch(patched_predict_func, return_value=predict_fixture())
    @mock.patch(patched_read_machine_func, return_value=normal_machine_fixture())
    def test_post_state_returns_500_when_request_is_invalid(self, *patch):
        expected = 500
        actual = self.app.post('/state')

        self.assertEqual(expected, actual.status_code)

        actual = self.app.post('/state', json={'values': []})
        self.assertEqual(expected, actual.status_code)

        actual = self.app.post('/state', json={'name': ''})
        self.assertEqual(expected, actual.status_code)
