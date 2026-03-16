# OpenClaw 部署指南

> 将金瓶梅软件作坊部署到 OpenClaw Gateway 并与 Telegram 集成

---

## 前置条件

- OpenClaw Gateway 已安装并运行（v2026.2.x+）
- 已有一个 Telegram 账号用于管理 Bot
- 本项目的 FastAPI 中间件可以正常运行

---

## 第一步：创建 Telegram Bot

通过 BotFather（@BotFather）创建 5 个 Bot：

| Bot 名称 | 用途 | 建议用户名 |
|----------|------|-----------|
| 规划师 Bot | 任务规划与分配 | `@{项目名}PlannerBot` |
| 执行者-1 Bot | 执行具体任务 | `@{项目名}Executor1Bot` |
| 执行者-2 Bot | 执行具体任务 | `@{项目名}Executor2Bot` |
| 审查者 Bot | 审查成果质量 | `@{项目名}ReviewerBot` |
| 巡查者 Bot | 监控系统健康 | `@{项目名}PatrolBot` |

**操作步骤：**
```
1. 在 Telegram 搜索 @BotFather
2. 发送 /newbot
3. 按提示输入 Bot 名称和用户名
4. 保存返回的 Bot Token
5. 重复以上步骤创建 5 个 Bot
```

## 第二步：创建 Telegram Forum Supergroup

```
1. 在 Telegram 创建一个新的 Group（超级群组）
2. 群组设置 → 启用 "Topics"（话题模式）
3. 创建以下话题（Topic）：
   - 📋 规划频道
   - 🔧 执行频道-1
   - 🔧 执行频道-2
   - 📝 审查频道
   - 🚨 巡查频道
4. 将 5 个 Bot 都设为群管理员
5. 记录下群组 ID 和各话题的 Thread ID
```

> **获取群组 ID**：将 Bot 拉入群组后，访问：
> `https://api.telegram.org/bot<TOKEN>/getUpdates`
> 找到 `chat.id` 字段（负数）

## 第三步：部署 OpenClaw 配置

```bash
# 1. 复制配置模板
cp deploy/openclaw.example.jsonc ~/.openclaw/openclaw.json

# 2. 编辑配置文件，替换以下占位符：
#    - <TELEGRAM_BOT_TOKEN_PLANNER> 等 5 个 Bot Token
#    - <YOUR_FORUM_GROUP_ID> 为群组 ID
#    - <WEBHOOK_SECRET_TOKEN> 为自定义的 Webhook 密钥
```

## 第四步：部署 Agent Workspace

```bash
# 1. 创建各 Agent 的 workspace 目录
mkdir -p ~/.openclaw/workspace-planner
mkdir -p ~/.openclaw/workspace-executor-1
mkdir -p ~/.openclaw/workspace-executor-2
mkdir -p ~/.openclaw/workspace-reviewer
mkdir -p ~/.openclaw/workspace-patrol

# 2. 复制 SOUL.md 到对应 workspace
cp deploy/soul/planner/SOUL.md   ~/.openclaw/workspace-planner/SOUL.md
cp deploy/soul/executor/SOUL.md  ~/.openclaw/workspace-executor-1/SOUL.md
cp deploy/soul/executor/SOUL.md  ~/.openclaw/workspace-executor-2/SOUL.md
cp deploy/soul/reviewer/SOUL.md  ~/.openclaw/workspace-reviewer/SOUL.md
cp deploy/soul/patrol/SOUL.md    ~/.openclaw/workspace-patrol/SOUL.md

# 3. 复制 skills 到各 workspace（按需选择）
# Planner 需要的 skills
cp -r skills/task-planner-skill ~/.openclaw/workspace-planner/skills/

# Executor 需要的 skills
cp -r skills/task-executor-skill ~/.openclaw/workspace-executor-1/skills/
cp -r skills/task-executor-skill ~/.openclaw/workspace-executor-2/skills/

# Reviewer 需要的 skills
cp -r skills/task-reviewer-skill ~/.openclaw/workspace-reviewer/skills/

# Patrol 需要的 skills
cp -r skills/task-patrol-skill ~/.openclaw/workspace-patrol/skills/
```

## 第五步：配置 FastAPI 中间件

在项目的 `config.yaml` 中添加 OpenClaw 集成配置：

```yaml
# OpenClaw Gateway 集成
openclaw:
  gateway_url: "http://localhost:4160"  # Gateway 地址
  webhook_token: "你的Webhook密钥"       # 需与 openclaw.json 中 hooks.token 一致
  webhook_enabled: true                  # 启用事件驱动通知
```

## 第六步：启动验证

```bash
# 1. 启动 FastAPI 中间件
python -m uvicorn app.main:app --host 0.0.0.0 --port 6565

# 2. 重启 OpenClaw Gateway
openclaw gateway restart

# 3. 验证 Agent 绑定
openclaw agents list --bindings

# 4. 验证 Telegram 连接
openclaw channels status --probe

# 5. 测试 Webhook
curl -X POST http://localhost:4160/hooks/agent \
  -H "Authorization: Bearer <WEBHOOK_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"agentId":"planner","event":"test","payload":{"message":"Webhook测试"}}'
```

## 注意事项

### ⚠️ Telegram Bot API 限制

> Bot 在群聊中**看不到**其他 Bot 发送的消息。这是 Telegram 平台级限制。
> Agent 间通信必须通过 OpenClaw 内建的 `sessions_send` 工具完成。

### ⚠️ Announce 刷屏

Agent 间通信时，中间消息也会通过 announce 推送到 Telegram。缓解方式：
- 保持 A2A 消息简洁，减少来回
- 在 SOUL.md 中明确告知 Agent 不要回发确认消息

### ⚠️ Session Visibility

`tools.sessions.visibility: "all"` 是全局设置，所有 Agent 都能看到其他 Agent 的 session。
单用户场景下这是正常的，多用户场景需要评估安全性。

---

## 架构图

```
┌──────────────────────────────────────────────────┐
│             Telegram Forum Supergroup            │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐│
│  │规划频道│ │执行频道│ │审查频道│ │ 巡查频道   ││
│  └───┬────┘ └───┬────┘ └───┬────┘ └─────┬──────┘│
└──────┼──────────┼──────────┼────────────┼────────┘
       │          │          │            │
┌──────┼──────────┼──────────┼────────────┼────────┐
│      ▼          ▼          ▼            ▼        │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐  │
│  │Planner │ │Executor│ │Reviewer│ │  Patrol   │  │
│  │  Bot   │ │  Bot   │ │  Bot   │ │   Bot     │  │
│  └───┬────┘ └───┬────┘ └───┬────┘ └─────┬────┘  │
│      │  sessions_send  sessions_send     │       │
│      │◄─────────┼──────────┼─────────────┤       │
│      ├──────────►          │             │       │
│      │          ├──────────►             │       │
│      │          │          ├─────────────►       │
│      │                                           │
│  OpenClaw Gateway (sessions_send 内部通信)        │
└──────────────────┬───────────────────────────────┘
                   │ Webhook (/hooks/agent)
                   ▼
┌──────────────────────────────────────────────────┐
│  FastAPI 任务调度中间件                            │
│  ┌─────────────────────────────────────────────┐ │
│  │ sub_task_service → fire_event → webhook     │ │
│  │ review_service  → fire_event → webhook      │ │
│  │ escalation_service → fire_event → webhook   │ │
│  └─────────────────────────────────────────────┘ │
│  数据库: SQLite  │  端口: 6565                    │
└──────────────────────────────────────────────────┘
```
