import torch
from tinysglang.layers.base import BaseOP


class Linear(BaseOP):
    def __init__(self, in_features: int, out_features: int):
        self.weight = torch.randn(out_features, in_features)
        self.bias = torch.zeros(out_features)
        self._cache = None  # 私有属性，不会被导出

    def forward(self, x):
        return x @ self.weight.T + self.bias


class MLP(BaseOP):
    def __init__(self):
        self.fc1 = Linear(10, out_features=20)
        self.fc2 = Linear(20, 5)

    def forward(self, x):
        x = self.fc1.forward(x)
        return self.fc2.forward(x)


# 使用
model = MLP()
state = model.state_dict()

print(state)
# 输出: dict_keys(['fc1.weight', 'fc1.bias', 'fc2.weight', 'fc2.bias'])
