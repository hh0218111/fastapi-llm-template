# fastapi-llm-template

AI 应用开发 · 阶段 1「工程基础」的 FastAPI 后端模板项目。
之后所有项目（流式 ChatBot / RAG 知识库 / Agent）都长在它上面。

## 项目结构

```
app/
  schemas/    # Pydantic 请求/响应模型（API 边界校验）
  api/        # 路由（D4 起）
  core/       # 配置 / 日志 / 异常（D2 起）
scripts/      # 独立实验脚本（D3 asyncio demo）
tests/        # pytest 测试（D4 起）
```

## 快速开始

```bash
uv sync                             # 安装依赖
uv run python app/schemas/chat.py   # 跑 Pydantic 校验 demo
uv run uvicorn app.main:app --reload   # D4 起可用
```

## 设计决策

- **依赖管理用 uv**：锁文件进 Git，环境可复现（`uv sync` 一键重建）。
- **应用项目非库**：`[tool.uv] package = false`，不做打包安装，`uv run` 直跑。
- **API 边界用 Pydantic**：外部数据一律过校验；内部轻量结构才用 dataclass。
- **异常精确捕获**：如 `ValidationError`，禁止裸 `except Exception` 吞错。

（D7 收尾时补全：架构图、鉴权链路、SSE 流式说明、踩坑记录）
