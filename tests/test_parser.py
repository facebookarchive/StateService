#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

from unittest import TestCase

from ..state_service.parser import Parser


class TestParser(TestCase):

    def setUp(self):
        self.parser = Parser()

    def tearDown(self):
        self.parser = None

    def test_parser(self):
        options = self.parser.parser.parse_args(
            ['--chart', 'states.yaml',
             '--debug',
             '--host', 'www.facebook.com',
             '--port', '22111',
             ]
        )

        expected = 'states.yaml'
        actual = options.chart
        self.assertEqual(expected, actual)

        actual = options.debug
        self.assertTrue(actual)

        expected = 'www.facebook.com'
        actual = options.host
        self.assertEqual(expected, actual)

        expected = 22111
        actual = options.port
        self.assertEqual(expected, actual)
