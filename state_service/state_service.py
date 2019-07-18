#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

import json
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

    GET and PUT methods act on a state machine that is used to describe states,
    for example, when one state transitions to another state.

    GET /state?state=:state determines if a state, :state, is the current
    state.
    POST /state determines the state that the requesting machine is in using
    a previously trained ML model for prediction.
    PUT /state?state=:state updates the state, :state, and determines if it
    should transition to another state.
    """

    def __init__(self, parser):
        self._logger = None
        self._machine = None
        self._options = None
        self._parser = parser

    def create_state(self):
        """
        Predicts the state that the requesting machine is in.

        The request references the name of a model and values that the model
        requires to make a prediction. The values are metrics reported by the
        the requesting machines.

        Returns:
            A state that describes the requesting machine (with a 200 HTTP
            response), or,
            A 500 HTTP response if an error occurs in the prediction process
        """

        error_response = Response(
            response=json.dumps({}),
            mimetype='application/json',
            status=500,
        )
        if not request.is_json:
            self.logger.error(f'POST /state: Request must be JSON formatted')
            return error_response

        if 'name' not in request.json:
            self.logger.error(f'POST /state: Missing name')
            return error_response

        if 'values' not in request.json:
            self.logger.error(f'POST /state: Missing values')
            return error_response

        name, values = request.json.get('name'), request.json.get('values')

        try:
            state = self.machine.predict(name, values)
            data = {'state': state}
            return Response(
                response=json.dumps(data),
                mimetype='application/json',
                status=200,
            )
        except RuntimeError as e:
            self.logger.exception(f'POST /state: {str(e)}')
            return error_response

    def get_state(self):
        """
        Determines whether the current state matches the state passed in as a
        query parameter.

        Returns:
            A 200 HTTP response if :state is the current state,
            A 406 HTTP response if :state is not the current state, or,
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
            self.machine.update()
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
            self._logger = logging.getLogger(self.__class__.__name__)

        return self._logger

    @property
    def machine(self):
        if self._machine is None:
            self._machine = StateMachine(self.options)

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

    def _initialize(self):
        """
        Initializes the state machine to be served.

        A state machine is optional, since StateService can operate
        exclusively to serve queries of stored ML models from machines.
        """
        if self.options.machine:
            self.machine.build()


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


@app.route('/state', methods=['OPTIONS', 'POST'])
def create_state():
    return state_service.create_state()


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
        state_service._initialize()
        app.run(
            debug=debug, host=host, port=port, threaded=False,
        )
    except Exception:
        state_service.machine.save()
        return 1


if __name__ == '__main__':
    sys.exit(main())
