"""
结构化日志 —— 让日志「机器能读、人能看懂」

为什么不用 print / 默认 logging 文本格式？
- print 没有级别、没有时间、没有上下文，出了问题只能靠猜
- 默认文本格式是给眼睛看的，日志系统（ELK/Loki）解析它要靠正则，脆且难维护
- 一行一个 JSON：字段化之后就能按 trace_id / level / module 精确检索和告警

trace_id 是什么？
一次用户请求从进门到出门的唯一编号。请求经过 5 个函数、10 条日志，
靠它全串起来——线上排查「这个用户到底哪一步挂了」全靠它。
"""

import contextvars
import json
import logging
import sys

from app.core.config import get_settings

# 为什么用 ContextVar 而不是模块级全局变量？
# asyncio 并发时，多个协程共享同一个线程/进程，全局变量会被互相覆盖（A 的 trace_id 串到 B 的日志里）。
# ContextVar 是「协程/任务上下文私有」的变量：每个请求有自己的一份，asyncio 天然支持。
# 默认值 "system" 表示「非请求上下文」（启动阶段、后台任务）的日志。
trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="system")


class JSONFormatter(logging.Formatter):
    """把 LogRecord 转成一行 JSON"""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            # ts：人肉排查时看的可读时间
            "ts": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            # timestamp：机器用的精确时间戳（排序、计算耗时都靠它）
            "timestamp": record.created,
            # 当前协程上下文的请求 ID，没有就是 system
            "trace_id": trace_id_var.get(),
            "level": record.levelname,
            "message": record.getMessage(),
            # 出问题时能直接定位到「哪个文件、哪个函数、第几行」
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 只有真正带异常堆栈的日志才附加，避免每行都塞一个 null
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)

        # ensure_ascii=False：中文原样输出，别转成 \u4f60\u597d 这种鬼东西
        return json.dumps(log_record, ensure_ascii=False)


def setup_logging() -> None:
    """
    全局日志初始化 —— 只在应用入口调用一次。

    幂等保护（if logger.handlers: return）：
    - uvicorn --reload 会重复导入模块，不挡住的话同一条日志会打印 N 次
    - 这也是新手最常见的坑：「为什么我的日志每条都出现两遍？」
    """
    settings = get_settings()
    logger = logging.getLogger()
    logger.setLevel(settings.log_level)

    if logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    # uvicorn 自带的 access log 是纯文本、量大且格式不统一，先压到 WARNING。
    # D5 会用中间件写我们自己的结构化访问日志（含耗时、trace_id），比它更有用。
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
