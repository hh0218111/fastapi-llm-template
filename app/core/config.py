"""
配置中心 —— 全项目所有「环境相关」的开关、密钥、参数的唯一入口

为什么不直接 os.getenv 到处读？
1. 类型校验：pydantic 会把 "false"/"30" 转成 bool/int，写错了启动就报错（fail fast）
2. 单一入口：想知道项目依赖哪些配置，打开这个文件就够了，不用全局搜索
3. 默认值兜底：本地开发不配 .env 也能跑；生产用环境变量覆盖
4. 可测试：测试时可以构造 Settings(secret_key="test") 注入，不依赖本机环境
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 字段名大小写不敏感：.env 里写 APP_NAME，这里就能接到
    app_name: str = "fastapi-llm-template"

    # 密钥默认值故意写成「一眼假」的开发值——逼你在部署时想起来要换
    # 生产环境靠 .env / 系统环境变量覆盖，绝不能把真密钥写进代码提交
    secret_key: str = "dev-only-change-me"

    log_level: str = "INFO"

    # env_file：自动加载项目根目录的 .env
    # extra="ignore"：.env 里存在、但这里没定义的字段直接忽略
    #（比如 .env.example 里预留的 JWT_* 配置，D5 鉴权时再加字段启用）
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """
    单例：整个进程只解析一次 .env，之后所有调用拿到同一个对象。

    为什么重要：
    - 每次 new Settings() 都会重新读文件，路由多了就是无谓 IO
    - 同一个进程里配置必须一致，不能这个模块读到旧值、那个模块读到新值
    - 测试时可 get_settings.cache_clear() 清缓存后重新构造，实现配置切换
    """
    return Settings()
