#
# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import tripy as tp

from typing import Union, Optional, get_origin, get_args, ForwardRef, List
from tripy.common import datatype
import inspect


def tensor_builder(init, dtype, namespace):
    if init is None:
        out = tp.ones(dtype=namespace[dtype], shape=(3, 2))
        out.eval()
        return out
    elif not isinstance(init, tp.Tensor):
        return init
    out = tp.cast(init, dtype=namespace[dtype])
    out.eval()
    return out


def dtype_builder(init, dtype, namespace):
    return namespace[dtype]


def tensor_list_builder(init, dtype, namespace):
    if init is None:
        out = [tp.ones(shape=(3, 2), dtype=namespace[dtype]) for _ in range(2)]
    else:
        out = [tp.cast(tens, dtype=namespace[dtype]) for tens in init]
    for t in out:
        t.eval()
    return out


def device_builder(init, dtype, namespace):
    if init is None:
        return tp.device("gpu")
    return init


def default_builder(init, dtype, namespace):
    return init


find_func = {
    "tripy.Tensor": tensor_builder,
    "tripy.Shape": tensor_builder,
    "tripy.dtype": dtype_builder,
    datatype.dtype: dtype_builder,
    List[Union["tripy.Tensor"]]: tensor_list_builder,
    "tripy.device": device_builder,
}

"""
default_constraints_all: This dictionary helps set specific constraints and values for parameters. These constraints correspond to the type hint of each parameter.
Some type have default values, so you might not need to pass other_constraints for every operation.
If there is no default, you must specify an initialization value, or the testcase may fail.
The dictionary's keys must be the name of the function that they are constraining and the value must be what the parameter should be initialized to.
Here is the list of parameter types that have defaults or work differently from other types:
    - tensor - default: tp.ones(shape=(3,2)). If init is passed then value must be in the form of a list. Example: "scale": tp.Tensor([1,1,1]) or "scale": tp.ones((3,3))
    - dtype - default: no default. Dtype parameters will be set using dtype_constraints input so using default_constraints_all will not change anything.
    - list/sequence of tensors - default: [tp.ones((3,2)),tp.ones((3,2))]. Example: "dim": [tp.ones((2,4)),tp.ones((1,2))].
        This will create a list/sequence of tensors of size count and each tensor will follow the init and shape value similar to tensor parameters.
    - device - default: tp.device("gpu"). Example: {"device": tp.device("cpu")}.
All other types do not have defaults and must be passed to the verifier using default_constraints_all.
"""
default_constraints_all = {
    "__rtruediv__": {"self": 1},
    "__rsub__": {"self": 1},
    "__radd__": {"self": 1},
    "__rpow__": {"self": 1},
    "__rmul__": {"self": 1},
    "softmax": {"dim": 1},
    "concatenate": {"dim": 0},
    "expand": {"sizes": tp.Tensor([3, 4]), "input": tp.ones((3, 1))},
    "full": {"shape": tp.Tensor([3]), "value": 1},
    "full_like": {"value": 1},
    "flip": {"dim": 1},
    "gather": {"dim": 0, "index": tp.Tensor([1])},
    "iota": {"shape": tp.Tensor([4])},
    "__matmul__": {"self": tp.ones((2, 3))},
    "transpose": {"dim0": 0, "dim1": 1},
    "permute": {"perm": [1, 0]},
    "quantize": {"scale": tp.Tensor([1, 1, 1]), "dim": 0},
    "dequantize": {"scale": tp.Tensor([1, 1, 1]), "dim": 0},
    "sum": {"dim": 0},
    "all": {"dim": 0},
    "any": {"dim": 0},
    "max": {"dim": 0},
    "prod": {"dim": 0},
    "mean": {"dim": 0},
    "var": {"dim": 0},
    "argmax": {"dim": 0},
    "argmin": {"dim": 0},
    "reshape": {"shape": tp.Tensor([6])},
    "squeeze": {"input": tp.ones((3, 1)), "dims": (1)},
    "__getitem__": {"index": 2},
    "split": {"indices_or_sections": 2},
    "unsqueeze": {"dim": 1},
    "masked_fill": {"value": 1},
    "ones": {"shape": tp.Tensor([3, 2])},
    "zeros": {"shape": tp.Tensor([3, 2])},
    "arange": {"start": 0, "stop": 5},
    "repeat": {"repeats": 2, "dim": 0},
    "convolution": {
        "input": tp.ones((1, 3, 5, 5)),
        "weight": tp.ones((1, 3, 3, 3)),
        "padding": ((0, 0), (0, 0)),
        "stride": [1, 1],
        "groups": 1,
        "lhs_dilation": [1, 1],
        "rhs_dilation": [1, 1],
    },
}


def create_obj(func_obj, func_name, param_name, param_dtype, namespace):
    # If type is an optional or union get the first type.
    # Get names and type hints for each param.
    func_sig = inspect.signature(func_obj)
    param_dict = func_sig.parameters
    param_type_annot = param_dict[param_name]
    init = None
    # Check if there is a value in default_constraints_all for func_name and param_name and use it.
    default_constraints = default_constraints_all.get(func_name, None)
    if default_constraints != None:
        other_constraint = default_constraints.get(param_name, None)
        if other_constraint is not None:
            init = other_constraint
    # If parameter had a default then use it otherwise skip.
    if init is None and param_type_annot.default is not param_type_annot.empty:
        # Checking if not equal to None since default can be 0 or similar.
        if param_type_annot.default != None:
            init = param_type_annot.default
    param_type = param_type_annot.annotation
    while get_origin(param_type) in [Union, Optional]:
        param_type = get_args(param_type)[0]
        # ForwardRef refers to any case where type hint is a string.
        if isinstance(param_type, ForwardRef):
            param_type = param_type.__forward_arg__
    create_obj_func = find_func.get(param_type, default_builder)
    if create_obj_func:
        namespace[param_name] = create_obj_func(init, param_dtype, namespace)
        return namespace[param_name]
