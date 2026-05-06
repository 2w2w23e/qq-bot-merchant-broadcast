"""定时任务注册模块"""
from nonebot import get_bot
from nonebot.log import logger

try:
    from nonebot_plugin_apscheduler import scheduler
except ImportError:
    scheduler = None
    logger.warning("[远行商人] nonebot-plugin-apscheduler 未安装，定时功能不可用")

from .config import MerchantConfig

_last_post_id: list[str] = [""]


def setup_scheduler(config: MerchantConfig):
    if scheduler is None:
        logger.error("[远行商人] 无法注册定时任务：apscheduler 不可用")
        return

    hours = config.merchant_schedule_hours or [9, 13, 17, 21]
    hour_str = ",".join(str(h) for h in hours)
    logger.info("[远行商人] 注册定时任务，每天 %s:00 执行", hour_str)

    if config.merchant_test_mode:
        t = config.merchant_test_group or (config.merchant_groups[0] if config.merchant_groups else "未配置")
        logger.info("[远行商人] 测试模式：定时消息只发往群 %s", t)

    @scheduler.scheduled_job(
        "cron",
        hour=hour_str,
        minute=0,
        id="merchant_broadcast",
        replace_existing=True,
    )
    async def _broadcast_job():
        logger.info("[远行商人] 定时任务触发")
        try:
            bot = get_bot()
        except Exception as e:
            logger.warning("[远行商人] 获取 Bot 实例失败（未连接？）: %s", e)
            return

        from . import broadcast_merchant
        await broadcast_merchant(bot, config, _last_post_id)
