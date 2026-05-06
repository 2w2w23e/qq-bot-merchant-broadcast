"""道具信息解析模块"""
import re
from typing import Optional
from nonebot.log import logger


def parse_merchant_items(content: str) -> list[str]:
    """
    从帖子正文中提取道具列表。

    支持以下格式：
      本轮更新道具如下：
      1. 魔力果
      2. 恶系粉尘

      或：
      本轮出售道具：魔力果、恶系粉尘、命运指引书

      或：
      当前远行商人在卖：魔力果 恶系粉尘
    """
    if not content:
        return []

    items = []

    # ── 策略1：「道具如下/出售道具/商人在卖」后的编号列表 ──────────────
    # 匹配触发词，然后提取后续的编号条目
    trigger_pattern = re.compile(
        r"(?:本轮(?:更新|出售)?道具(?:如下)?[：:「]?|远行商人在卖[：:]?|当前.*?在卖[：:]?)"
        r"([\s\S]{0,600})",
        re.IGNORECASE,
    )
    m = trigger_pattern.search(content)
    if m:
        block = m.group(1)
        # 编号列表：1. xxx 或 ①xxx 或 •xxx
        numbered = re.findall(
            r"(?:^|\n)\s*(?:\d+[.、．]|[①②③④⑤⑥⑦⑧⑨⑩]|[-•·])\s*(.+)",
            block,
        )
        if numbered:
            items = [item.strip() for item in numbered if item.strip()]
            logger.debug(f"[远行商人] 策略1 提取到 {len(items)} 个道具")
            return items

        # 同行逗号/顿号/空格分隔：本轮出售道具：魔力果、恶系粉尘
        # 取触发词后第一行
        first_line = block.strip().split("\n")[0].strip()
        # 去掉首尾标点
        first_line = re.sub(r"^[：:「『\s]+|[」』\s]+$", "", first_line)
        if first_line:
            # 按顿号/逗号/空格分割
            split_items = re.split(r"[，,、\s]+", first_line)
            split_items = [i.strip() for i in split_items if i.strip()]
            if split_items:
                logger.debug(f"[远行商人] 策略1-内联 提取到 {len(split_items)} 个道具")
                return split_items

    # ── 策略2：宽泛匹配「道具：」后内容 ──────────────────────────────
    wide_pattern = re.compile(
        r"道具[：:\s]+([^\n]{2,100})"
    )
    for wm in wide_pattern.finditer(content):
        line = wm.group(1).strip()
        split_items = re.split(r"[，,、\s]+", line)
        split_items = [i.strip() for i in split_items if len(i.strip()) >= 2]
        if split_items:
            logger.debug(f"[远行商人] 策略2 提取到 {len(split_items)} 个道具")
            return split_items

    logger.info("[远行商人] 未能从帖子中提取道具信息")
    return []
