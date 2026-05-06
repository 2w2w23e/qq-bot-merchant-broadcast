"""插件配置

为避免 pydantic-settings 自动将逗号分隔字符串当成 JSON 解析，
把 list 类型字段统一用 str 接收，再手动切割。
"""
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MerchantConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # 以字符串接收，避免 pydantic-settings 尝试将逗号分隔字符串当 JSON 解析
    merchant_groups: str = ""
    merchant_schedule_hours: str = "9,13,17,21"

    xhh_user_id: str = "98021738"
    xhh_request_timeout: int = 15
    xhh_retry_times: int = 3

    merchant_test_mode: bool = False
    merchant_test_group: str = ""

    # 解析后的实际列表（model_validator 填充，不写入 .env）
    groups: list[str] = Field(default_factory=list, exclude=True)
    schedule_hours: list[int] = Field(default_factory=lambda: [9, 13, 17, 21], exclude=True)

    @model_validator(mode="after")
    def _parse_list_fields(self) -> "MerchantConfig":
        self.groups = [
            g.strip() for g in self.merchant_groups.split(",") if g.strip()
        ]
        raw_hours = [
            int(h.strip())
            for h in self.merchant_schedule_hours.split(",")
            if h.strip().isdigit()
        ]
        self.schedule_hours = raw_hours if raw_hours else [9, 13, 17, 21]
        return self
