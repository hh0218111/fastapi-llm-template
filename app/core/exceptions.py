"""
异常分层 —— 业务错误和系统错误，分开对待

为什么不直接抛 HTTPException？
- 业务代码（service 层）不应该知道「HTTP」这个概念，它只该说「没找到」「没权限」
- 直接抛 HTTPException 会让 service 层和 Web 框架焊死，换成 CLI / 消息队列就废了
- 散落各处的 try/except 会越写越多；分层后，全项目只在入口注册一次处理器

分层设计：
AppError（基类，所有业务异常的共同契约）
├── NotFoundError      404  资源不存在
├── AuthenticationError 401  未认证 / token 无效
└── UpstreamServiceError 502  上游（LLM API、第三方服务）挂了
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """
    所有业务异常的基类。子类固化 code 和 status_code，调用方只传 message。

    code 是给前端/调用方看的稳定错误码（不要随文案改），
    status_code 是 HTTP 语义，message 是给人看的中文描述。
    这三者分离，前端才能写 if (res.error.code === "NOT_FOUND") 这种稳定逻辑。
    """

    def __init__(self, code: str, status_code: int, message: str):
        self.code = code
        self.status_code = status_code
        self.message = message
        # 让父类 Exception 也持有 message，str(exc) / repr 时才有内容
        super().__init__(self.message)


class NotFoundError(AppError):
    def __init__(self, message: str = "资源未找到"):
        super().__init__(code="NOT_FOUND", status_code=404, message=message)


class AuthenticationError(AppError):
    def __init__(self, message: str = "认证失败"):
        super().__init__(code="AUTHENTICATION_FAILED", status_code=401, message=message)


class UpstreamServiceError(AppError):
    # 502 Bad Gateway：上游服务（LLM API 超时、第三方接口 5xx）出问题
    # 这个异常第 3 周接真模型时会高频使用
    def __init__(self, message: str = "上游服务异常"):
        super().__init__(code="UPSTREAM_SERVICE_ERROR", status_code=502, message=message)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    全局异常处理器：任何路由里 raise AppError 的子类，都会被 FastAPI 接住丢到这里。

    这样业务代码里只写 `raise NotFoundError("会话不存在")`，
    不用关心 HTTP 响应长什么样——统一格式只在这里维护一份。

    日志级别按状态码区分（关键设计）：
    - 4xx（404/401）：预期内的业务错误，用 warning，不打堆栈（打堆栈只会刷屏）
    - 5xx（502）：系统级问题，用 error，后续排查需要上下文
    """
    log = logger.error if exc.status_code >= 500 else logger.warning
    log("业务异常 | code=%s status=%d message=%s", exc.code, exc.status_code, exc.message)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )
