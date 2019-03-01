#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

import argparse


def argparse_fixture():
    return (
        argparse.Namespace(
            config='/var/opt/state_service/conf',
            machine='/var/opt/state_service/machine.yaml',
            models='/var/opt/state_service/models',
        ),
        []
    )


def async_machine_fixture():
    return {
        'current_state': 'state_1',
        'states': [{
            'name': 'state_1',
            'func': 'time',
            'target': {
                'name': 'state_2',
                'when': {
                    'key': 'clock',
                    'value': '3000-01-01T02:00:00',
                },
            },
        }, {
            'name': 'state_2',
            'func': 'time',
            'target': {
                'name': 'state_3',
                'when': {
                    'key': 'clock',
                    'value': '3000-01-01T02:00:10',
                },
            },
        }, {
            'name': 'state_3',
        }],
    }


def async_state_fixture():
    return {
        'name': 'state_1',
        'func': 'time',
        'target': {
            'name': 'state_2',
            'when': {
                'key': 'clock',
                'value': '3000-01-01T02:00:10',
            },
        },
    }


def deserialize_model_fixture():
    """
    Returns a deserialized version of an instance of
    the Model class. This simulates the idea that a
    model instance would be serialized and loaded
    from disk.
    """
    class Model:

        def predict(self, values):
            return [1]

    return Model()


def models_fixture():
    return {
        'fixture': {
            'name': 'fixture',
            'team': 'state_service',
            'model': 'fixture.pkl',
            'states': [
                'walk',
                'run',
                'jump',
            ],
        },
    }


def normal_machine_fixture():
    return {
        'current_state': 'state_1',
        'states': [{
            'name': 'state_1',
            'func': 'increment',
            'current': {
                'key': 'count',
                'value': 0,
            },
            'target': {
                'name': 'state_2',
                'when': {
                    'key': 'count',
                    'value': 2,
                },
            },
        }, {
            'name': 'state_2',
            'func': 'increment',
            'current': {
                'key': 'count',
                'value': 0
            },
            'target': {
                'name': 'state_3',
                'when': {
                    'key': 'count',
                    'value': 1,
                },
            },
        }, {
            'name': 'state_3',
        }],
    }


def normal_state_fixture():
    return {
        'name': 'state_1',
        'func': 'increment',
        'current': {
            'key': 'count',
            'value': 0,
        },
        'target': {
            'name': 'state_2',
            'when': {
                'key': 'count',
                'value': 2,
            },
        },
    }


def predict_fixture():
    return ['run']
