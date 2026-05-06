"""定时任务注册模块"""
from nonebot import get_bot, get_driver
from nonebot.log import logger

try:
    from nonebot_plugin_apscheduler import scheduler
except ImportError:
    scheduler = None
    logger.warning("[远行商人] nonebot-plugin-apscheduler 未安装，定时功能不可用")

from .config import MerchantConfig

# 用列表包装，实现跨函数的可变引用（去重用）
_last_post_id: list[str] = [""]


def setup_scheduler(config: MerchantConfig):
    """根据配置注册定时任务"""
    if scheduler is None:
        logger.error("[远行商人] 无法注册定时任务：apscheduler 不可用")
        return

    hours = config.merchant_schedule_hours
    if not hours:
        hours = [9, 13, 17, 21]

    hour_str = ",".join(str(h) for h in hours)
    logger.info(f"[远行商人] 注册定时任务，每天 {hour_str}:00 执行")

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
            logger.warning(f"[远行商人] 获取 Bot 实例失败（未连接？）: {e}")
            return

        # 延迟导入避免循环依赖
        from . import broadcast_merchant
        await broadcast_merchant(bot, config, _last_post_id)
