"""插件配置"""
from pydantic import BaseModel, field_validator
from nonebot import get_plugin_config
from nonebot.log import logger
import os


class MerchantConfig(BaseModel):
    """远行商人插件配置，从 .env 读取"""

    # 目标群号列表（字符串形式，防止大数字精度丢失）
    merchant_groups: list[str] = []

    # 小黑盒用户 UID
    xhh_user_id: str = "98021738"

    # 定时推送小时列表（24小时制）
    merchant_schedule_hours: list[int] = [9, 13, 17, 21]

    # 请求超时（秒）
    xhh_request_timeout: int = 15

    # 失败重试次数
    xhh_retry_times: int = 3

    @field_validator("merchant_groups", mode="before")
    @classmethod
    def parse_groups(cls, v):
        """支持逗号分隔字符串或列表"""
        if isinstance(v, str):
            return [g.strip() for g in v.split(",") if g.strip()]
        return v

    @field_validator("merchant_schedule_hours", mode="before")
    @classmethod
    def parse_hours(cls, v):
        """支持逗号分隔字符串或列表"""
        if isinstance(v, str):
            return [int(h.strip()) for h in v.split(",") if h.strip()]
        return v

    class Config:
        env_prefix = ""
        case_sensitive = False
        extra = "ignore"
