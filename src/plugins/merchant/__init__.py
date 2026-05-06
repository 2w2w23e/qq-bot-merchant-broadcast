"""远行商人播报插件入口"""
from nonebot import get_driver, on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.log import logger

from .config import MerchantConfig
from .parser import parse_merchant_items
from .scheduler import setup_scheduler
from .spider import fetch_latest_post

plugin_config = MerchantConfig()
driver = get_driver()


@driver.on_startup
async def _startup_register_scheduler():
    logger.info(
        f"[远行商人] 插件启动，测试模式={plugin_config.merchant_test_mode}，"
        f"测试群={plugin_config.merchant_test_group or '未设置'}"
    )
    setup_scheduler(plugin_config)


# ── 群内指令 ──────────────────────────────────────────────────
merchant_cmd = on_command("商人", aliases={"查商人", "远行商人"}, priority=5, block=True)
test_cmd     = on_command("测试商人", aliases={"商人测试", "测试远行商人"}, priority=5, block=True)
send_cmd     = on_command("发送商人", aliases={"立即发送商人", "商人发送"}, priority=5, block=True)


@merchant_cmd.handle()
async def handle_merchant_query():
    """立即查询当前远行商人（仅回复当前群，不推送）"""
    post = await fetch_latest_post(
        plugin_config.xhh_user_id,
        plugin_config.xhh_request_timeout,
        plugin_config.xhh_retry_times,
    )
    if not post:
        await merchant_cmd.finish("暂时没有拿到远行商人信息，请稍后再试。")
        return

    items = parse_merchant_items(post["content"])
    if not items:
        await merchant_cmd.finish("最新帖子里暂未识别到远行商人售卖道具。")
        return

    await merchant_cmd.finish(_format_message(items))


@test_cmd.handle()
async def handle_merchant_test(event: GroupMessageEvent):
    """测试模式：预览抓取结果，不实际发送（需 MERCHANT_TEST_MODE=true）"""
    if not plugin_config.merchant_test_mode:
        await test_cmd.finish(
            "当前未开启测试模式。\n"
            "请在 .env 中设置：MERCHANT_TEST_MODE=true"
        )
        return

    await test_cmd.send("🔍 正在抓取最新帖子...")

    post = await fetch_latest_post(
        plugin_config.xhh_user_id,
        plugin_config.xhh_request_timeout,
        plugin_config.xhh_retry_times,
    )
    if not post:
        await test_cmd.finish("❌ 测试失败：未能抓取到最新帖子，请检查网络或 XHH_USER_ID 配置。")
        return

    items = parse_merchant_items(post["content"])
    target_group = plugin_config.merchant_test_group or str(event.group_id)

    if not items:
        preview = (post.get("content") or "")[:120].replace("\n", " ")
        await test_cmd.finish(
            "⚠️ 【测试完成，但未识别到道具】\n"
            f"帖子ID：{post.get('post_id', '未知')}\n"
            f"标题：{post.get('title', '无标题')}\n"
            f"正文预览：{preview or '（空）'}\n"
            "\n💡 如需强制发送，使用 /发送商人 指令"
        )
        return

    await test_cmd.finish(
        "✅ 【测试模式预览（未发送）】\n"
        f"目标群：{target_group}\n"
        f"帖子ID：{post.get('post_id', '未知')}\n"
        f"发布时间：{post.get('publish_time', '未知')}\n"
        "────────────────\n"
        f"{_format_message(items)}\n"
        "\n💡 确认无误后发送 /发送商人 立即推送到目标群"
    )


@send_cmd.handle()
async def handle_merchant_send(bot: Bot, event: GroupMessageEvent):
    """测试模式下立即抓取并真实发送到目标群（不受去重限制）"""
    if not plugin_config.merchant_test_mode:
        await send_cmd.finish(
            "当前未开启测试模式。\n"
            "请在 .env 中设置：MERCHANT_TEST_MODE=true"
        )
        return

    await send_cmd.send("📤 正在抓取并立即发送...")

    post = await fetch_latest_post(
        plugin_config.xhh_user_id,
        plugin_config.xhh_request_timeout,
        plugin_config.xhh_retry_times,
    )
    if not post:
        await send_cmd.finish("❌ 抓取失败，无法发送。")
        return

    items = parse_merchant_items(post["content"])
    if not items:
        await send_cmd.finish("⚠️ 未识别到道具信息，发送取消。")
        return

    msg = _format_message(items)

    # 目标群优先级：测试专用群 > groups 第一个 > 当前群
    if plugin_config.merchant_test_group:
        target_groups = [plugin_config.merchant_test_group]
    elif plugin_config.groups:
        target_groups = [plugin_config.groups[0]]
    else:
        target_groups = [str(event.group_id)]

    results = []
    for gid in target_groups:
        try:
            await bot.send_group_msg(group_id=int(gid), message=msg)
            results.append(f"  ✅ 群 {gid} 发送成功")
            logger.info(f"[远行商人] 测试立即发送 → 群 {gid}")
        except Exception as e:
            results.append(f"  ❌ 群 {gid} 发送失败: {e}")
            logger.error(f"[远行商人] 测试立即发送失败 群 {gid}: {e}")

    await send_cmd.finish("📪 【立即发送完毕】\n" + "\n".join(results))


def _format_message(items: list[str]) -> str:
    return f"当前远行商人在卖：{'、'.join(items)}"


async def broadcast_merchant(bot: Bot, config: MerchantConfig, last_post_id: list[str]):
    """定时任务调用的广播函数"""
    post = await fetch_latest_post(
        config.xhh_user_id,
        config.xhh_request_timeout,
        config.xhh_retry_times,
    )
    if not post:
        logger.warning("[远行商人] 爬取失败，跳过本次推送")
        return

    if post["post_id"] == last_post_id[0]:
        logger.info(f"[远行商人] 帖子 {post['post_id']} 已推送过，跳过")
        return

    items = parse_merchant_items(post["content"])
    if not items:
        logger.info("[远行商人] 未找到道具信息，跳过本次推送")
        return

    # 测试模式：只推送测试群或首个群
    target_groups = list(config.groups)
    if config.merchant_test_mode:
        if config.merchant_test_group:
            target_groups = [config.merchant_test_group]
        elif target_groups:
            target_groups = [target_groups[0]]
        logger.info(f"[远行商人] 测试模式，本次仅推送到：{target_groups}")

    if not target_groups:
        logger.warning("[远行商人] 未配置可推送群号，跳过")
        return

    last_post_id[0] = post["post_id"]
    msg = _format_message(items)

    for group_id in target_groups:
        try:
            await bot.send_group_msg(group_id=int(group_id), message=msg)
            logger.info(f"[远行商人] 已推送到群 {group_id}")
        except Exception as e:
            logger.error(f"[远行商人] 推送群 {group_id} 失败: {e}")
