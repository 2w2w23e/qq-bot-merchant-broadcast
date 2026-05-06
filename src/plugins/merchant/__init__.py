"""远行商人播报插件入口"""
from nonebot import get_driver, on_command, on_keyword
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot.log import logger

from .config import MerchantConfig
from .spider import fetch_latest_post
from .parser import parse_merchant_items
from .scheduler import setup_scheduler

# 读取配置
plugin_config = MerchantConfig()

# 注册定时任务
driver = get_driver()

@driver.on_startup
async def _():
    logger.info("[远行商人] 插件启动，注册定时任务...")
    setup_scheduler(plugin_config)


# ── 主动查询指令 ──────────────────────────────────────
merchant_cmd = on_command("商人", aliases={"查商人", "远行商人"}, priority=5)

@merchant_cmd.handle()
async def handle_merchant_query(bot: Bot, event: GroupMessageEvent):
    """群内触发立即查询"""
    await merchant_cmd.send("🔍 正在查询远行商人信息，请稍候...")

    post = await fetch_latest_post(plugin_config.xhh_user_id, plugin_config.xhh_request_timeout)
    if not post:
        await merchant_cmd.finish("❌ 暂时无法获取远行商人信息，请稍后再试。")
        return

    items = parse_merchant_items(post["content"])
    if not items:
        await merchant_cmd.finish(
            f"📭 最新帖子（{post['title'][:30]}）中未找到道具信息。"
        )
        return

    msg = _format_message(post, items)
    await merchant_cmd.finish(msg)


def _format_message(post: dict, items: list[str]) -> str:
    """格式化推送消息"""
    items_text = "\n".join(f"  {i+1}. {item}" for i, item in enumerate(items))
    return (
        f"🧙‍♂️ 【远行商人来了！】\n"
        f"📅 发布时间：{post.get('publish_time', '未知')}\n"
        f"📦 本轮出售道具如下：\n"
        f"{items_text}"
    )


# 暴露给 scheduler 使用
async def broadcast_merchant(bot: Bot, config: MerchantConfig, last_post_id: list):
    """定时任务调用的广播函数"""
    post = await fetch_latest_post(config.xhh_user_id, config.xhh_request_timeout)
    if not post:
        logger.warning("[远行商人] 爬取失败，跳过本次推送")
        return

    # 去重：同一帖子只推送一次
    if post["post_id"] == last_post_id[0]:
        logger.info(f"[远行商人] 帖子 {post['post_id']} 已推送过，跳过")
        return

    items = parse_merchant_items(post["content"])
    if not items:
        logger.info("[远行商人] 未找到道具信息，跳过本次推送")
        return

    last_post_id[0] = post["post_id"]
    msg = _format_message(post, items)

    for group_id in config.merchant_groups:
        try:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
            logger.info(f"[远行商人] 已推送到群 {group_id}")
        except Exception as e:
            logger.error(f"[远行商人] 推送群 {group_id} 失败: {e}")
