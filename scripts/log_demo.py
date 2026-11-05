"""
日志 + 异常演示脚本（脱离 Web 服务，单独跑：uv run python scripts/log_demo.py）

为什么要手动处理 sys.path？
直接 `python scripts/log_demo.py` 运行时，Python 会把「脚本所在目录 scripts/」放进 sys.path[0]，
项目根目录不在搜索路径里，所以 `import app` 会报 ModuleNotFoundError。
把项目根目录手动插进 sys.path，脚本才能复用 app/ 下的模块。
（另一种做法是 `uv run python -m scripts.log_demo`，以模块方式运行就不会有这个问题）
"""

import json
import logging
import os
import sys

# 把项目根目录（scripts/ 的上一级）加入模块搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 注意：这两行导入必须写在 sys.path 调整之后，否则 app 包还不可见
from app.core.exceptions import NotFoundError
from app.core.logging import setup_logging, trace_id_var


def main() -> None:
    # 1. 初始化日志（会读 settings 里的 LOG_LEVEL）
    setup_logging()
    logger = logging.getLogger("demo")

    # 2. 模拟中间件设置 trace_id：
    #    真实场景里这一段由 D5 的中间件在每个请求进门前自动生成并 set，
    #    这里手动设一下，验证 trace_id 能出现在后面每一行日志里
    trace_id_var.set("req-12345-abcde")

    logger.info("测试日志1：准备抛出异常...")

    # 3. 模拟业务层抛出的异常，并演示「日志 + 返回体」两步走
    try:
        raise NotFoundError("会话不存在，id: 999")
    except NotFoundError as e:
        # logger.exception() 是「在 except 块里记录异常」的惯用法：
        # 等价于 logger.error(..., exc_info=True)，但意图更明确、更不容易写错
        logger.exception("捕获到异常: %s", e.message)

        # 脚本里没有 FastAPI 的全局处理器，手动模拟一下最终返回给前端的 JSON
        #（真实服务里这一步由 app_error_handler 自动完成）
        response = {"error": {"code": e.code, "message": e.message}}
        print("\n--- 最终返回给前端的 JSON ---")
        print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
