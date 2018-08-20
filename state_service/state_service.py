#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

import logging
from flask import Flask
from flask import request
from flask import Response

from .logger import configure_logger
from .parser import Parser
from .state_chart import StateChart


class StateService(object):
    """
    Configures a Flask application using command-line arguments and includes
    response methods for each endpoint.

    Each method acts on a state chart that is used to describe states, for
    example, when one state transitions to another state.

    GET /state?state=:state determines if a state, :state, is the current
    state.
    PUT /state?state=:state updates the state, :state and determines if it
    should transition to another state.
    """

    def __init__(self, parser):
        self._chart = None
        self._logger = None
        self._options = None
        self._parser = parser

    def get_state(self):
        """
        Returns 204 or 406 depending on whether the current state matches
        the state passed in as a query parameter.

        Returns:
            A 200 HTTP response if :state is the current state,
            A 406 HTTP response otherwise
        """
        state = request.args.get('state')

        if state is None:
            self.logger.error('GET /state: Missing :state query parameter')
            return Response('', status=406)

        if self.chart.current_state.name == state:
            self.logger.info(f'GET /state: {state} is current state')
            return Response(f'{state}', status=200)

        self.logger.info(f'GET /state: {state} is not current state')
        return Response('', status=406)

    def update_state(self):
        """
        Updates the current state and determines if the state should
        transition to a new state.

        Returns:
            A 200 HTTP response if :state was updated,
            A 406 HTTP response if :state was not updated, or,
            A 500 HTTP response if :state could not be updated
        """
        state = request.args.get('state')

        if state is None:
            self.logger.error('PUT /state: Missing :state query parameter')
            return Response('', status=500)

        if self.chart.current_state.name == state:
            if self.chart.current_state.is_end_state:
                self.logger.info(f'PUT /state: {state} is final state')
                return Response('', status=406)
            try:
                self.chart.current_state.update()
            except RuntimeError as e:
                self.logger.error(f'PUT /state: Unable to update {state} state')
                return Response('', status=500)
            else:
                self.logger.info(f'PUT /state: Updated {state} state')
                return Response(f'{state}', status=200)

        self.logger.info(f'PUT /state: {state} is not current state')
        return Response('', status=406)

    @property
    def chart(self):
        if self._chart is None:
            self._chart = StateChart(self.options.chart)

        return self._chart

    @property
    def logger(self):
        if self._logger is None:
            self._logger = logging.getLogger(__name__)

        return self._logger

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


if __name__ == '__main__':
    options = state_service.options
    debug = options.debug
    host = options.host
    logger_path = options.logger
    port = options.port
    configure_logger(path=logger_path)
    app.run(debug=debug, host=host, port=port)
