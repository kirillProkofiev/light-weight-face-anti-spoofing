'''MIT License

Copyright (C) 2019-2020 Intel Corporation
 
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom
the Software is furnished to do so, subject to the following conditions:
 
The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.
 
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES
OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.'''

import torch
import torch.nn as nn
import math
import torch.nn.functional as F

class Conv2d_cd(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1,
                 padding=1, dilation=1, groups=1, bias=False, theta=0):

        super(Conv2d_cd, self).__init__() 
        self.theta = 0
        self.theta_limit = theta
        self.bias = bias or None
        self.stride = stride
        self.groups = groups
        if self.groups > 1:
            self.weight = nn.Parameter(kaiming_init(out_channels, in_channels//in_channels, kernel_size))
        else:
            self.weight = nn.Parameter(kaiming_init(out_channels, in_channels, kernel_size))
        self.padding = padding
        self.i = 0

    def forward(self, x):
        if self.training and self.theta < self.theta_limit and self.theta_limit != 0:
            self.theta = -0.000000000476190*self.i**2+0.000074761904762*self.i-0.000000000000003
            self.i +=1
        out_normal = F.conv2d(input=x, weight=self.weight, bias=self.bias, stride=self.stride, padding=self.padding, groups=self.groups)
        if math.fabs(self.theta - 0.0) < 1e-8:
            return out_normal
        else:
            [C_out, C_in, kernel_size, kernel_size] = self.weight.shape
            kernel_diff = self.weight.sum(2).sum(2)
            kernel_diff = kernel_diff[:, :, None, None]
            out_diff = F.conv2d(input=x, weight=kernel_diff, bias=self.bias, stride=self.stride, padding=0, groups=self.groups)
            if self.i in set((0, 1000, 7000, 10000)):
                print(self.theta, end=' ')
            return out_normal - self.theta * out_diff

def kaiming_init(C_out, C_in, k):
    return torch.randn(C_out, C_in, k, k)*math.sqrt(2./C_in)