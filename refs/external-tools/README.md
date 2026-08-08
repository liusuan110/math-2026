# 外部工具参考索引

这里放置与数学建模比赛工作流相关、但不是往年赛题工程的外部工具项目。

## Beacon

- 本地路径：`refs/external-tools/Beacon/`
- 来源：https://github.com/123-qw-as/Beacon
- 定位：面向数学建模比赛的端到端多智能体自动化流水线。
- 本地状态：已按普通文件下载，已移除其嵌套 `.git` 目录。
- 主要依赖：Python 3.11-3.13、Node.js 18+、uv、OpenAI-compatible LLM API。
- 安装状态：Python 依赖已通过 `uv sync` 安装到 `refs/external-tools/Beacon/.venv/`；前端依赖已通过 `npm install` 安装到 `node_modules/`。
- 启动地址：http://localhost:5173
- 后端命令：`.env` 中已配置为使用主工作区的 `.venv/Scripts/uv.exe run math-agent`。
- API 配置：`.env` 已预置 DeepSeek 模型和端点配置，但没有写入密钥；购买 API 后添加 `OPENAI_API_KEY` 和 `DEEPSEEK_API_KEY` 即可。

### DeepSeek 配置说明

当前 `.env` 采用 LiteLLM 的 DeepSeek provider 写法：

```text
OPENAI_API_BASE=https://api.deepseek.com
OPENAI_API_KEY=你的 DeepSeek API Key
DEEPSEEK_API_KEY=你的 DeepSeek API Key
MATH_AGENT_DEFAULT_MODEL=deepseek/deepseek-v4-flash
MATH_AGENT_CODER_MODEL=deepseek/deepseek-v4-flash
MATH_AGENT_STRONG_MODEL=deepseek/deepseek-v4-pro
MATH_AGENT_FIGURE_MODEL=deepseek/deepseek-v4-pro
```

DeepSeek 官方文档显示 `deepseek-chat` / `deepseek-reasoner` 旧模型名将在 2026-07-24 后弃用，因此这里优先使用 `deepseek-v4-flash` 和 `deepseek-v4-pro`。若购买 API 时控制台展示的模型名有变化，以 DeepSeek 控制台和官方文档为准。

注意：Beacon 的 `/api/env/check` 通用环境检测只检查系统 PATH 中是否存在 `uv`，不会读取 `.env` 里的绝对后端命令；因此 UI 里可能显示 uv 未安装，但实际后端命令已配置为可用路径。

### 值得学习的部分

1. `src/math_agent/nodes/`：拆题、建模、代码、敏感性、图表、写作、评审、LaTeX 编译等节点拆分。
2. `src/math_agent/prompts/`：不同阶段的提示词模板。
3. `src/math_agent/rag/`：模型库和优秀论文片段的检索增强设计。
4. `frontend/`：比赛流水线的本地 Web UI 组织方式。
5. `tests/fixtures/`：样例题面 JSON，可参考其题目结构化方式。

### 使用建议

暂不建议直接并入当前比赛主流程或直接运行生成论文。更适合把它当作工程样本，学习：

- 如何把比赛拆成可审查阶段。
- 如何在建模、代码、图表、论文之间设置质量检查。
- 如何让图表按“数据、模型、结果、敏感性”语义进入正文。
- 如何在人类确认后再进入最终 PDF 编译。
