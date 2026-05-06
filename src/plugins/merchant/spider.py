"""小黑盒爬虫模块"""
import asyncio
import random
import re
from typing import Optional

import httpx
from nonebot.log import logger

# 小黑盒 API 接口
# 用户动态列表接口（公开帖子）
_API_URL = "https://api.xiaoheihe.cn/bbs/app/api/general/v1/link_list"
_PROFILE_URL = "https://www.xiaoheihe.cn/app/user/profile/{uid}"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.xiaoheihe.cn/",
    "Origin": "https://www.xiaoheihe.cn",
}


async def fetch_latest_post(
    user_id: str,
    timeout: int = 15,
    retry: int = 3,
) -> Optional[dict]:
    """
    爬取小黑盒用户最新帖子。

    Returns:
        dict with keys: post_id, title, content, publish_time
        or None if failed.
    """
    params = {
        "uid": user_id,
        "limit": 5,
        "offset": 0,
        "type": "post",  # 只拉帖子类型
    }

    for attempt in range(1, retry + 1):
        try:
            async with httpx.AsyncClient(
                headers=_HEADERS,
                timeout=timeout,
                follow_redirects=True,
            ) as client:
                resp = await client.get(_API_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

            post = _extract_post(data)
            if post:
                logger.info(f"[远行商人] 爬取成功，帖子ID: {post['post_id']}")
                return post

            logger.warning(f"[远行商人] 第 {attempt} 次：响应数据无有效帖子")

        except httpx.HTTPStatusError as e:
            logger.warning(f"[远行商人] 第 {attempt} 次请求 HTTP 错误: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.warning(f"[远行商人] 第 {attempt} 次请求失败: {e}")
        except Exception as e:
            logger.error(f"[远行商人] 第 {attempt} 次未知错误: {e}")

        if attempt < retry:
            delay = random.uniform(2.0, 5.0)
            logger.info(f"[远行商人] {delay:.1f}s 后重试...")
            await asyncio.sleep(delay)

    return None


def _extract_post(data: dict) -> Optional[dict]:
    """从 API 响应中提取最新帖子信息"""
    try:
        # 小黑盒 API 结构：data.result.list[]
        items = data.get("data", {}).get("result", {}).get("list", [])

        if not items:
            # 备用路径：直接在 result 下
            items = data.get("result", {}).get("list", [])

        if not items:
            logger.debug(f"[远行商人] API 返回数据结构: {list(data.keys())}")
            return None

        latest = items[0]

        # 兼容多种字段名
        post_id = str(
            latest.get("post_id")
            or latest.get("id")
            or latest.get("heybox_id")
            or "unknown"
        )
        title = latest.get("title") or latest.get("name") or ""
        # 正文可能在 content / desc / plain_text 字段
        content = (
            latest.get("content")
            or latest.get("desc")
            or latest.get("plain_text")
            or ""
        )
        publish_time = (
            latest.get("create_time")
            or latest.get("publish_time")
            or latest.get("ctime")
            or ""
        )

        # 时间戳转可读格式
        if isinstance(publish_time, (int, float)) and publish_time > 0:
            import datetime
            dt = datetime.datetime.fromtimestamp(publish_time)
            publish_time = dt.strftime("%Y-%m-%d %H:%M")

        return {
            "post_id": post_id,
            "title": title,
            "content": content,
            "publish_time": str(publish_time),
        }

    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"[远行商人] 解析帖子结构失败: {e}")
        return None
