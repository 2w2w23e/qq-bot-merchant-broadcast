# 🧙 远行商人播报机器人

基于 [NoneBot2](https://nonebot.dev/) 的 QQ 群机器人，自动爬取小黑盒用户帖子，提取远行商人当前售卖道具信息，定时（09:00 / 13:00 / 17:00 / 21:00）推送到指定 QQ 群。

## 功能特性

- ✅ 定时爬取小黑盒用户主页最新帖子（4次/天）
- ✅ 智能提取「本轮更新道具」列表
- ✅ 去重推送，同一帖子只推送一次
- ✅ 支持群内主动查询指令（`/商人` 或 `查商人`）
- ✅ 支持多群广播
- ✅ 通过 `.env` 配置，无需改动代码

## 效果预览

```
🧙‍♂️ 【远行商人来了！】
📅 发布时间：2026-05-06 08:45
📦 本轮更新道具如下：
  1. 魔力果
  2. 恶系粉尘
  3. 命运指引书
```

## 目录结构

```
qq-bot-merchant-broadcast/
├── bot.py                  # NoneBot2 启动入口
├── .env.example            # 环境变量示例
├── pyproject.toml          # 项目依赖
├── requirements.txt        # pip 依赖
└── src/
    └── plugins/
        └── merchant/
            ├── __init__.py     # 插件入口，注册事件
            ├── spider.py       # 小黑盒爬虫
            ├── parser.py       # 道具信息解析
            ├── scheduler.py    # 定时任务
            └── config.py       # 配置读取
```

## 快速开始

### 1. 环境要求

- Python >= 3.10
- 已安装并运行 [go-cqhttp](https://docs.go-cqhttp.org/) 或兼容 OneBot v11 协议的适配器

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并修改：

```bash
cp .env.example .env
```

编辑 `.env`：

```dotenv
# go-cqhttp 连接地址（反向 WebSocket）
DRIVER=~fastapi+~websockets
HOST=0.0.0.0
PORT=8080

# 推送的目标群号（多个群用英文逗号分隔）
MERCHANT_GROUPS=123456789,987654321

# 小黑盒目标用户 UID
XHH_USER_ID=98021738

# 定时任务时间（24小时制，默认 9,13,17,21）
MERCHANT_SCHEDULE_HOURS=9,13,17,21
```

### 4. 启动机器人

```bash
python bot.py
```

## 群内指令

| 指令 | 说明 |
|------|------|
| `/商人` | 立即查询当前远行商人信息 |
| `查商人` | 同上（自然语言触发） |

## 注意事项

- 小黑盒网站可能有请求频率限制，爬虫已加入随机延迟，请勿修改为过高频率
- 若帖子为空或无道具信息，当次不推送
- 去重基于帖子 ID，重启后状态不保留（可扩展为持久化）

## License

MIT
