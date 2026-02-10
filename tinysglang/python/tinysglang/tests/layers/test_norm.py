import torch

# 设置设备（flashinfer 需要 CUDA）
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
dtype = torch.float16  # flashinfer 需要 float16 或 bfloat16
print(f"Using device: {device}, dtype: {dtype}")

# ============ 手动实现 RMSNorm 用于对比 ============
def manual_rmsnorm(x: torch.Tensor, weight: torch.Tensor, eps: float) -> torch.Tensor:
    """手动实现 RMSNorm 用于验证"""
    # 计算均方根 (RMS)
    rms = torch.sqrt(torch.mean(x ** 2, dim=-1, keepdim=True) + eps)
    # 归一化并缩放
    return (x / rms) * weight


# ============ 测试 RMSNorm ============
print("\n" + "=" * 50)
print("测试 RMSNorm")
print("=" * 50)

from tinysglang.layers.norm import RMSNorm

hidden_size = 8
eps = 1e-6

# 创建 RMSNorm 层
norm = RMSNorm(size=hidden_size, eps=eps)
# 初始化权重为全 1（方便对比）
norm.weight = torch.ones(hidden_size, device=device, dtype=dtype)

# 创建输入
x = torch.tensor([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]], device=device, dtype=dtype)
print(f"输入 x: {x}")
print(f"输入形状: {x.shape}")

# flashinfer 的结果
output = norm.forward(x)
print(f"\nflashinfer RMSNorm 输出: {output}")

# 手动计算对比
manual_output = manual_rmsnorm(x, norm.weight, eps)
print(f"手动计算 RMSNorm 输出: {manual_output}")

# 验证结果是否一致
print(f"\n结果是否接近: {torch.allclose(output, manual_output, atol=1e-3)}")


# ============ 测试 RMSNormFused ============
print("\n" + "=" * 50)
print("测试 RMSNormFused (带残差)")
print("=" * 50)

from tinysglang.layers.norm import RMSNormFused

fused_norm = RMSNormFused(size=hidden_size, eps=eps)
fused_norm.weight = torch.ones(hidden_size, device=device, dtype=dtype)

# 情况 1: 没有残差
x1 = torch.tensor([[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]], device=device, dtype=dtype)
out1, res1 = fused_norm.forward(x1, residual=None)
print(f"\n[无残差] 输入 x: {x1}")
print(f"[无残差] 输出: {out1}")
print(f"[无残差] 返回的残差 (原始x): {res1}")

# 情况 2: 有残差 (融合 add + rmsnorm)
x2 = torch.tensor([[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], device=device, dtype=dtype)
residual = torch.tensor([[0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]], device=device, dtype=dtype)
print(f"\n[有残差] 输入 x: {x2}")
print(f"[有残差] 输入 residual: {residual}")

# 手动计算预期结果
expected_residual = residual + x2  # 先相加
expected_out = manual_rmsnorm(expected_residual, fused_norm.weight, eps)
print(f"\n[手动计算] residual + x = {expected_residual}")
print(f"[手动计算] RMSNorm(residual + x) = {expected_out}")

# flashinfer 融合操作 (原地修改!)
out2, res2 = fused_norm.forward(x2, residual=residual)
print(f"\n[flashinfer] 输出 x: {out2}")
print(f"[flashinfer] 输出 residual: {res2}")

print(f"\n融合操作结果是否正确: {torch.allclose(out2, expected_out, atol=1e-3)}")


# ============ 查看 state_dict ============
print("\n" + "=" * 50)
print("查看 state_dict (可保存的参数)")
print("=" * 50)

print(f"RMSNorm state_dict keys: {list(norm.state_dict().keys())}")
print(f"RMSNormFused state_dict keys: {list(fused_norm.state_dict().keys())}")
