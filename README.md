# 🧙 远行商人播报机器人

基于 [NoneBot2](https://nonebot.dev/) 的 QQ 群机器人，自动爬取小黑盒用户帖子，提取远行商人当前售卖道具，定时（09:00 / 13:00 / 17:00 / 21:00）推送到指定 QQ 群。

## 功能特性

- ✅ 定时爬取小黑盒用户主页最新帖子（4次/天）
- ✅ 智能提取「本轮更新道具」列表
- ✅ 去重推送，同一帖子只推送一次
- ✅ 支持群内主动查询（`/商人` 或 `查商人`）
- ✅ **测试模式**：定时推送只发往测试群，不干扰正式群
- ✅ **测试指令** `/测试商人`：立即抓取并返回调试信息
- ✅ 通过 `.env` 配置，无需改动代码

## 效果预览

普通查询 / 定时推送：
```
当前远行商人在卖：魔力果、恶系粉尘、命运指引书
```

`/测试商人` 返回：
```
✅ 【测试模式预览】
将推送到群：123456789
帖子ID：99887766
发布时间：2026-05-06 08:45
────────────────
当前远行商人在卖：魔力果、恶系粉尘、命运指引书
```

## 目录结构

```
qq-bot-merchant-broadcast/
├── bot.py                  # NoneBot2 启动入口
├── .env.example            # 配置模板
├── pyproject.toml
├── requirements.txt
└── src/plugins/merchant/
    ├── __init__.py         # 指令注册 & 广播逻辑
    ├── config.py           # 配置读取（含测试模式）
    ├── spider.py           # 小黑盒爬虫
    ├── parser.py           # 道具信息解析
    └── scheduler.py        # 定时任务
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 `.env`

```bash
cp .env.example .env
```

常规模式：
```dotenv
MERCHANT_GROUPS=你的群号
MERCHANT_TEST_MODE=false
```

测试模式：
```dotenv
MERCHANT_GROUPS=群A,群B
MERCHANT_TEST_MODE=true
MERCHANT_TEST_GROUP=群A   # 留空则默认取第一个群
```

### 3. 启动

```bash
python bot.py
```

> 需要先启动 go-cqhttp 或兼容 OneBot v11 协议的适配器并连接到 8080 端口。

## 群内指令

| 指令 | 说明 |
|------|------|
| `/商人` | 立即查询当前远行商人信息 |
| `查商人` | 同上（自然语言触发）|
| `/测试商人` | 测试模式下立即抓取并返回调试信息 |

## 测试模式说明

| 配置项 | 作用 |
|--------|------|
| `MERCHANT_TEST_MODE=true` | 开启测试模式 |
| `MERCHANT_TEST_GROUP=群号` | 定时推送只发往此群 |
| 留空 `MERCHANT_TEST_GROUP` | 自动取 `MERCHANT_GROUPS` 第一个群 |

开发阶段建议开启测试模式，避免正式群收到调试消息。上线后改为 `false` 即可。

## 注意事项

- 小黑盒可能有请求频率限制，爬虫已加入随机延迟，请勿修改为高频
- 去重基于帖子 ID，重启后状态不保留

## License

MIT
