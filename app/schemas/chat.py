from pydantic import BaseModel, Field, ValidationError


class ChatMessage(BaseModel):
    role: str = Field(..., description="角色: user 或 assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="用户输入")
    session_id: str | None = None
    temperature: float = Field(0.7, ge=0, le=2)


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


# 测试代码（uv run python app/schemas/chat.py 即可看到效果）
if __name__ == "__main__":
    # 成功示例
    req = ChatRequest(message="你好", temperature=1.0)
    print("✅ 校验成功:", req.model_dump())

    # 失败示例：精确捕获 ValidationError，别裸 except Exception
    try:
        ChatRequest(message="", temperature=3.0)
    except ValidationError as e:
        print("❌ 校验失败:", e)
