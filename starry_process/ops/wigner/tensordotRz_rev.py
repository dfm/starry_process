# -*- coding: utf-8 -*-
from ..base_op import BaseOp
from theano import gof
import theano
import theano.tensor as tt

__all__ = ["tensordotRzRevOp"]


class tensordotRzRevOp(BaseOp):
    func_file = "./tensordotRz_rev.cc"
    func_name = "APPLY_SPECIFIC(tensordotRz_rev)"

    def make_node(self, M, theta, bf):
        in_args = [
            tt.as_tensor_variable(arg).astype(tt.config.floatX)
            for arg in [M, theta, bf]
        ]
        out_args = [
            tt.TensorType(
                dtype=tt.config.floatX, broadcastable=[False, False]
            )(),
            tt.TensorType(dtype=tt.config.floatX, broadcastable=[False,])(),
        ]
        return gof.Apply(self, in_args, out_args)

    def infer_shape(self, node, shapes):
        K = shapes[0][0]
        return ([K, self.N], [K,])
