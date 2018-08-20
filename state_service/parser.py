#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

import argparse


class Parser(object):
    """
    Parses command-line arguments that configure StateService.
    """

    def __init__(self):
        self._options = None
        self._parser = None

    @property
    def options(self):
        """
        Parses command-line arguments.

        Returns:
            the command-line arguments parsed as a Namespace object.
        """
        if self._options is None:
            self._options, __ = self.parser.parse_known_args()

        return self._options

    @property
    def parser(self):
        if self._parser is None:
            self._configure_parser()

        return self._parser

    def _configure_parser(self):
        """
        Initializes an ArgumentParser.

        Returns:
            an instance of argparse.ArgumentParser, configured to expect
            arguments.
        """
        if self._parser is None:
            self._parser = argparse.ArgumentParser(prog='state_service',
                                                   fromfile_prefix_chars='@',
                                                   )
            self._parser.add_argument('--chart',
                                      type=str,
                                      required=False,
                                      default='/tmp/chart.yaml',
                                      help='the state chart for the tier',
                                      )
            self._parser.add_argument('--debug',
                                      action='store_true',
                                      default=False,
                                      help='start server in debug mode',
                                      )
            self._parser.add_argument('--host',
                                      type=str,
                                      required=False,
                                      default='127.0.0.1',
                                      help='the host that serves StateService',
                                      )
            self._parser.add_argument('--logger',
                                      type=str,
                                      required=False,
                                      default='logger.yaml',
                                      help='configuration file for logging',
                                      )
            self._parser.add_argument('--port',
                                      type=int,
                                      required=False,
                                      default=5000,
                                      help='the port that StateService listens to',
                                      )
