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

import re
import tripy as tp
from tripy.frontend.trace import Trace
from tripy.flat_ir.ops import MaxOp
from tripy.flat_ir.ops.base import FlatIRFunction


class TestMaxOp:
    def test_str(self):
        a = tp.Tensor([3.0, 4.0], name="a")
        b = tp.Tensor([5.0, 2.0], name="b")
        out = tp.maximum(a, b)
        out.name = "out"

        trace = Trace([out])
        flat_ir = trace.to_flat_ir()

        func_max = flat_ir.ops[-1]
        assert isinstance(func_max, FlatIRFunction)

        max_op = func_max.ops[-1]
        broadcast_a = func_max.ops[-3]
        broadcast_b = func_max.ops[-2]
        assert isinstance(max_op, MaxOp)
        assert re.match(
            r"t_inter[0-9]+: \[rank=\(1\), dtype=\(float32\), loc=\(gpu:0\)\] = DynamicBroadcastOp\(t_inter[0-9]+, t_inter[0-9]+, broadcast_dim=\[0\]\)",
            str(broadcast_a),
        )
        assert re.match(
            r"t_inter[0-9]+: \[rank=\(1\), dtype=\(float32\), loc=\(gpu:0\)\] = DynamicBroadcastOp\(t_inter[0-9]+, t_inter[0-9]+, broadcast_dim=\[0\]\)",
            str(broadcast_b),
        )
        assert re.match(
            r"t_inter[0-9]+: \[rank=\(1\), dtype=\(float32\), loc=\(gpu:0\)\] = MaxOp\(t_inter[0-9]+, t_inter[0-9]+\)",
            str(max_op),
        )
