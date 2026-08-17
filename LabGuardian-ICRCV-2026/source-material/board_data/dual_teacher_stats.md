# Dual-teacher Candidate Pool Summary

## Teacher-level ratios

| Teacher | Success rate | Citation rate | Usable rate | Downgraded rate | Avg latency |
|---|---:|---:|---:|---:|---:|
| DeepSeek-V3 | 99.76% | 69.46% | 69.46% | 30.3% | 2555.2 ms |
| Qwen3-32B | 82.78% | 56.78% | 56.78% | 26.01% | 7152.95 ms |

## Overlap-set coverage

| Metric | Ratio |
|---|---:|
| DeepSeek usable coverage | 67.77% |
| Qwen usable coverage | 56.78% |
| Dual-teacher pooled coverage | 82.42% |
| Both usable | 42.12% |
| DeepSeek-only gain | 25.64% |
| Qwen-only gain | 14.65% |
| Neither usable | 17.58% |

## Key takeaway

- Dual-teacher pooled coverage improves usable coverage by 14.65 percentage points over DeepSeek alone on the overlap set.
- Qwen contributes an extra 14.65% long-tail coverage beyond the stable teacher branch.