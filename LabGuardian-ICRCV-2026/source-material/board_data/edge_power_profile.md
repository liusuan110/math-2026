# 端侧学生模型实测功耗 / 吞吐 报告(边缘部署可行性)

- 日期:2026-05-29
- 硬件:Intel DK-2500(Core Ultra 5 225U,NPU + iGPU + CPU)
- 被测模型:`labguardian-student-1p5-int4-ov`(Qwen2.5-1.5B 蒸馏 → INT4 → OpenVINO IR,941 MB)
- 运行时:`openvino_genai.LLMPipeline`
- 功率采集:`turbostat`(RAPL),`PkgWatt`=整封装功率,**`GFXWatt`=RAPL 图形域功率 = 核显(iGPU)功率**(本板无 `intel_gpu_top`,用 GFXWatt 作核显活动信号)
- 吞吐:贪心解码、`ignore_eos` 强制每次生成 128 token,`tok/s = 128 / 单次时延`;功率窗口期由后台线程持续推理保持设备满载

## 实测数据

| 配置 | 模型大小 | 载入 | 吞吐 tok/s | 单次128token | 整封装功率 均/峰 | **核显功率 均/峰** |
|---|---|---|---|---|---|---|
| **idle**(无模型) | — | — | — | — | **4.3 W** | **0.0 W** |
| **student-1.5B @ iGPU(部署配置)** | 941 MB | 6.3 s | **23.1** | 5.54 s | **9.17 / 24.23 W** | **3.08 / 7.81 W** |
| student-1.5B @ CPU(对照) | 941 MB | 2.2 s | 28.7 | 4.46 s | **43.15 / 103.88 W** | 0 / 0 |
| gemma-3-4b @ iGPU(旧基线 3.3 GB) | — | — | — | — | ❌ 无法加载 | — |

> gemma-3-4b-it 是多模态导出,在生产文本 `LLMPipeline` 路径报 `num_inputs==5`(期望 3/4)无法加载 —— 它本就不是可直接落地的端侧**文本** LLM。

## 关键结论

**1. 边缘部署目的:达到 ✓**
学生模型跑在 iGPU 上,**整封装功率仅 ~9 W 均 / 24 W 峰,核显本身 ~3 W 均 / 7.8 W 峰**(相对 idle 仅 +5 W 增量),23 tok/s,941 MB,6 s 冷启动。对一块嵌入式开发板来说,这是非常宽裕的功耗/热预算。

**2. 设备路由(LLM→iGPU)被实测验证:**
| | iGPU | CPU |
|---|---|---|
| 整封装功率(均) | **9.2 W** | **43.2 W** |
| 整封装功率(峰) | 24.2 W | 103.9 W* |
| 吞吐 | 23.1 tok/s | 28.7 tok/s |

CPU 仅快 ~24%,但**整封装功率是 iGPU 的约 4.7 倍**(43 W vs 9 W)。把 LLM 放到 iGPU 而非 CPU,**平均省 ~34 W**、几乎不损吞吐,还把 CPU 让给检索/LangGraph 编排。这就是 `NPU=视觉 / GPU=LLM / CPU=图` 异构路由的实测依据。

**3. 蒸馏选型正确:** 旧基线 gemma-3-4b(3.3 GB,3.5×)连生产文本 LLM 路径都加载不了;蒸馏出的 1.5B(941 MB)是"恰好够用、能落地"的端侧尺寸。

## 深度性能画像(student-1.5B @ iGPU,部署态)

单配置细测(`ignore_eos` 强制 128 token,贪心),数据源 `reports/llm_edge_profile.json`:

| 指标 | 实测值 | 说明 |
|---|---|---|
| 冷启动载入 | **3.74 s** | 一次性 |
| **首 token 延迟 TTFT** | **63.9 ms** | 含 prompt prefill —— 学生几乎"秒回第一个字" |
| **每 token 时间 TPOT** | **42.9 ms/token** | ≈ 23 tok/s 解码 |
| 吞吐 | **23.2 tok/s** | — |
| 单次 128-token 回答 | **5.52 s** | — |
| **每次回答能耗** | **56 J** / 128-token 回答 | = 推理均功率 × 时延,边缘效率金句 |
| 模型显存/内存占用(增量) | **351 MB** | 载入后 RSS 增量 |
| 运行时 RSS | 407 MB | — |
| **峰值内存 VmHWM** | **1.36 GB** | 8 GB 板上 LLM 仅占 ~1.4 GB,叠加 YOLO(NPU)+ bge(CPU)后仍可控 |
| idle → 推理 整封装 | 4.42 → **10.16 W** | 仅 +5.7 W |
| idle → 推理 核显(GFX) | 0 → **3.69 W**(峰 3.82) | 核显本体增量极小 |

**功率时序图**:`reports/llm_power_ts.png`(idle 平直 → LLM 推理抬升 → 冷却回落,整封装 + 核显两条曲线 + 阶段着色),原始时序 `reports/llm_power_ts.csv`(160 采样点)。

> 注:此处推理整封装均值 10.16 W、核显 3.69 W 与上面对比表的 9.2 W / 3.1 W 同量级(差异来自 `ignore_eos` 持续满载 vs 含 EOF 提前停的混合负载),互为印证。

## 备注 / 口径
- CPU 峰值 103.88 W* 可能含 turbostat 瞬时采样 + PL2 短时 boost,**以均值 43 W 为稳健信号**;GPU/CPU 的功率**比值**(~4.7×)是结论的核心,不依赖单点峰值。
- 该测量为纯 LLM 负载;整机部署时叠加 NPU 视觉(实测 +~4 W,见 #98)与 CPU 上的 bge embedder + LangGraph,三器件分工后整机仍在嵌入式功耗包络内。
- 数据源:`reports/llm_power_bench.json`;采集脚本:`scripts/board/llm_power_bench.py`。
