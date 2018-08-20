#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

import logging.config
import os
import yaml


def configure_logger(path=None, default_level=logging.INFO):
    """
    Configures the logger for StateService.
    """

    if os.path.exists(path):
        with open(path, 'rt') as f:
            try:
                config = yaml.safe_load(f.read())
                logging.config.dictConfig(config)
            except Exception as e:
                logging.basicConfig(level=default_level)
    else:
        logging.basicConfig(level=default_level)
