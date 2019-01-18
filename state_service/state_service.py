#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

import logging
import sys
from flask import Flask
from flask import request
from flask import Response

from .logger import configure_logger
from .parser import Parser
from .state_machine import StateMachine


class StateService(object):
    """
    Configures a Flask application using command-line arguments and includes
    response methods for each endpoint.

    Each method acts on a state machine that is used to describe states, for
    example, when one state transitions to another state.

    GET /state?state=:state determines if a state, :state, is the current
    state.
    PUT /state?state=:state updates the state, :state, and determines if it
    should transition to another state.
    """

    def __init__(self, parser):
        self._logger = None
        self._machine = None
        self._options = None
        self._parser = parser

    def get_state(self):
        """
        Determines whether the current state matches the state passed in as a
        query parameter.

        Returns:
            A 200 HTTP response if :state is the current state,
            A 406 HTTP response if :state is not the current state
            A 500 HTTP response if :state is missing
        """
        state = request.args.get('state')

        if state is None:
            self.logger.error('GET /state: Missing :state query parameter')
            return Response('', status=500)

        if self.machine.is_current_state(state):
            self.logger.info(f'GET /state: {state} is current state')
            return Response(f'{state}', status=200)

        self.logger.info(f'GET /state: {state} is not current state')
        return Response('', status=406)

    def update_state(self):
        """
        Updates the current state and determines if the state should
        transition to a new state.

        Asynchronous (scheduled) states are updated based on an internal
        clock, so the response to a PUT request when the state machine is
        asynchronous will be 500.

        Returns:
            A 200 HTTP response if :state was updated,
            A 406 HTTP response if :state was not updated, or,
            A 500 HTTP response if :state is missing or could not be
                updated
        """
        state = request.args.get('state')

        if state is None:
            self.logger.error('PUT /state: Missing :state query parameter')
            return Response('', status=500)

        if self.machine.did_end:
            self.logger.info(
                'PUT /state: {state}; the state machine is in its final state'
            )
            return Response('', status=500)

        if self.machine.is_async:
            self.logger.info(
                'PUT /state: {state}; an async state machine updates itself'
            )
            return Response('', status=500)

        if self.machine.is_current_state(state):
            if self.machine.update():
                self.machine.save()
                self.logger.info(f'PUT /state: Updated {state} state')
                return Response(f'{state}', status=200)
            else:
                self.logger.error(f'PUT /state: Unable to update {state} state')
                return Response('', status=500)

        self.logger.info(f'PUT /state: {state} is not current state')
        return Response('', status=406)

    @property
    def logger(self):
        if self._logger is None:
            self._logger = logging.getLogger(__name__)

        return self._logger

    @property
    def machine(self):
        if self._machine is None:
            self._machine = StateMachine(self.options.machine)
            self._machine.build()

        return self._machine

    @property
    def options(self):
        """
        Initializes a Namespace object with the CLI arguments.

        Returns:
            a Namespace object
        """
        if self._options is None:
            self._options = self._parser.options

        return self._options


"""
Initialize StateService and Flask app, but use placeholder methods that
return values from the StateService class.
"""
parser = Parser()
state_service = StateService(parser)
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True


@app.route('/state', methods=['OPTIONS', 'GET'])
def get_state():
    return state_service.get_state()


@app.route('/state', methods=['OPTIONS', 'PUT'])
def update_state():
    return state_service.update_state()


def main():
    options = state_service.options
    debug = options.debug
    host = options.host
    logger_path = options.logger
    port = options.port
    configure_logger(path=logger_path)

    try:
        app.run(debug=debug, host=host, port=port)
    except Exception:
        app.machine.save()
        return 1


if __name__ == '__main__':
    sys.exit(main())
