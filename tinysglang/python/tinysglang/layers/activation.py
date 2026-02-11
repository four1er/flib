from typing import TYPE_CHECKING

import torch


def silu_and_mul(x: torch.Tensor) -> torch.Tensor:
    from flashinfer import silu_and_mul

    return silu_and_mul(x)


def silu_and_mul_native(x: torch.Tensor) -> torch.Tensor:
    x1, x2 = x.chunk(2, dim=-1)
    silu_x1 = x1 * torch.sigmoid(x1)
    return silu_x1 * x2


__all__ = ["silu_and_mul"]
