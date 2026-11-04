"""
Pydantic 模型层 —— API 的「边界守卫」

为什么用 Pydantic 而不是 dataclass？
- 外部进来的数据（HTTP 请求、配置文件）一律不可信 → 需要运行时校验
- 校验失败自动抛 ValidationError，FastAPI 会转成 422 响应（带字段级错误信息）
- 自带序列化（model_dump）和反序列化（model_validate），和 JSON 无缝互转
- 纯内部、开发者自己保证正确的数据结构才用 dataclass（轻量无校验）
"""

from pydantic import BaseModel, Field, ValidationError


class ChatMessage(BaseModel):
    """单条对话消息（多轮对话历史的基本单元）"""

    # Field(...) 的 ... 表示必填项；description 会进 OpenAPI 文档（/docs 可见）
    role: str = Field(..., description="角色: user 或 assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """聊天请求体 —— POST /api/v1/chat 的入参校验"""

    # 约束即文档：min/max 同时防脏数据和恶意超长输入
    # 校验失败时 Pydantic 报错精确到字段，前端能直接展示
    message: str = Field(..., min_length=1, max_length=4000, description="用户输入")

    # 可选字段用 `X | None = None`（Python 3.10+ 写法，等价 Optional[str]）
    session_id: str | None = None

    # ge/le = 大于等于/小于等于 —— temperature 是采样温度，物理范围 [0, 2]
    temperature: float = Field(0.7, ge=0, le=2)


class TokenUsage(BaseModel):
    """LLM token 用量统计（成本核算用，第 2 周接真 API 时填真实数据）"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


# ---------- 校验自测（uv run python app/schemas/chat.py 即可看到效果） ----------
# 改完模型随手跑一下，成功/失败两条路径都验证 —— 比写完整测试快，比不测强
if __name__ == "__main__":
    # ① 成功路径：合法数据通过校验，model_dump() 转成 dict（方便发给 LLM API 或存库）
    req = ChatRequest(message="你好", temperature=1.0)
    print("✅ 校验成功:", req.model_dump())

    # ② 失败路径：message 为空 + temperature 超范围 → 一次报出两个字段错误
    # 注意：精确捕获 ValidationError，不要裸 except Exception（会吞掉真正的 bug）
    try:
        ChatRequest(message="", temperature=3.0)
    except ValidationError as e:
        print("❌ 校验失败:", e)
