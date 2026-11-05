"""
应用入口 —— 组装各模块的地方

初始化顺序不是随便排的：
1. settings 先读（后面所有模块都依赖配置）
2. logging 立即配（保证后面应用创建过程的日志也是 JSON 格式）
3. 最后创建 app 并注册处理器
"""

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exceptions import AppError, app_error_handler
from app.core.logging import setup_logging

# 先读配置，再建日志：日志的级别来自配置
settings = get_settings()
setup_logging()

app = FastAPI(title=settings.app_name)

# 注册全局异常处理器：
# 之后任何路由里 raise AppError 及其子类，FastAPI 都会自动交给 app_error_handler 处理，
# 业务代码里再也不需要写 try/except + JSONResponse。
app.add_exception_handler(AppError, app_error_handler)
