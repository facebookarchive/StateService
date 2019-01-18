#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#

import abc


class StateDelegate(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def did_enter_state(self, old_state, new_state):
        """
        System did transition from old state to
        new state.
        """
