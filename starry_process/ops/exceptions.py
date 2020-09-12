# -*- coding: utf-8 -*-
import numpy as np
from theano import gof
import theano.tensor as tt

__all__ = ["CheckBoundsOp"]


class CheckBoundsOp(tt.Op):
    """

    """

    def __init__(self, lower=-np.inf, upper=np.inf, name=None):
        self.lower = lower
        self.upper = upper
        if name is None:
            self.name = "parameter"
        else:
            self.name = name

    def make_node(self, *inputs):
        inputs = [tt.as_tensor_variable(inputs[0]).astype(tt.config.floatX)]
        outputs = [inputs[0].type()]
        return gof.Apply(self, inputs, outputs)

    def infer_shape(self, node, shapes):
        return shapes

    def perform(self, node, inputs, outputs):
        outputs[0][0] = np.array(inputs[0])
        if np.any((inputs[0] < self.lower) | (inputs[0] > self.upper)):
            low = np.where((inputs[0] < self.lower))[0]
            high = np.where((inputs[0] > self.upper))[0]
            if len(low):
                value = np.atleast_1d(inputs[0])[low[0]]
                sign = "<"
                bound = self.lower
            else:
                value = np.atleast_1d(inputs[0])[high[0]]
                sign = ">"
                bound = self.upper
            raise ValueError(
                "%s out of bounds: %f %s %f" % (self.name, value, sign, bound)
            )

    def grad(self, inputs, gradients):
        return [1.0 * gradients[0]]

    def R_op(self, inputs, eval_points):
        if eval_points[0] is None:
            return eval_points
        return self.grad(inputs, eval_points)
