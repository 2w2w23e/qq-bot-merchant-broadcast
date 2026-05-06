"""插件配置"""
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MerchantConfig(BaseSettings):
    """远行商人插件配置，从 .env 读取"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # 推送目标群列表
    merchant_groups: list[str] = Field(default_factory=list)

    # 小黑盒用户 UID
    xhh_user_id: str = "98021738"

    # 定时推送小时（24小时制）
    merchant_schedule_hours: list[int] = Field(default_factory=lambda: [9, 13, 17, 21])

    # 网络超时（秒）
    xhh_request_timeout: int = 15

    # 失败重试次数
    xhh_retry_times: int = 3

    # ── 测试模式 ──────────────────────────────────────
    # 开启后，定时推送只发往 merchant_test_group（或首个群）
    merchant_test_mode: bool = False

    # 测试专用群号（留空则取 MERCHANT_GROUPS 第一个群）
    merchant_test_group: str = ""

    @field_validator("merchant_groups", mode="before")
    @classmethod
    def parse_groups(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [g.strip() for g in v.split(",") if g.strip()]
        return v

    @field_validator("merchant_schedule_hours", mode="before")
    @classmethod
    def parse_hours(cls, v):
        if v is None:
            return [9, 13, 17, 21]
        if isinstance(v, str):
            return [int(h.strip()) for h in v.split(",") if h.strip()]
        return v
