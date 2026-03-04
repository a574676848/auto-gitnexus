---
name: jira-integration
description: 零依赖的 Jira CLI 辅助技能 (基于 Python 3)，专为 Jira Server 7.5.2 优化，提供智能打单、查询、更新、流转和删除工单的集成能力。
---

# Jira CLI Integration Skill (AI Agent 指南)

当用户要求你操作 Jira 上的工单时，**你必须严格按照以下流程和契约调用本目录下的 Python CLI 脚本**。

## 关键契约与工作流 (The Contract)

这些脚本位于 `scripts_py/` 目录下，采用纯 Python 3 编写，适配 **Jira Server 7.5.2 (v2 API)**。

### 第一步：身份认证与动态配置 (Authentication & Setup)

1. **触发条件**：
   - 第一次执行任何脚本。
   - 脚本返回 `"error_type": "MISSING_CREDENTIALS"`。
   - 脚本返回 `"error_type": "UNAUTHORIZED"`。

2. **行动**：
   - 停止后续操作，主动询问用户："由于你是首次使用（或凭据已失效），请提供你的 **Jira 域名 (Host)**、**账号 (Username)** 和 **密码/API Token** 以便我连接系统。"
   - 收到信息后，执行配置脚本：
     `python scripts_py/auth.py --domain "<Jira域名>" --user "<账号>" --token "<密码/Token>"`
   - 配置成功后，重新执行用户原本请求的操作。

### 第二步：识别意图并调度工具 (Dispatcher)

#### 意图 1：批量工单查询 (Search Issues)
- **脚本**：`python scripts_py/search.py --jql "<JQL>"`
- **用法**：将自然语言转为 JQL。Jira 7.x 不支持 `accountId` 过滤，请使用 `assignee = 'username'` 或 `reporter = 'username'`。

#### 意图 1.5：查看单个工单详情 (Get Single Issue)
- **脚本**：`python scripts_py/get_issue.py --issue "<KEY>"`
- **剧本**：用户说"看看这个单子"、"查一下 TEST-123"。它可以返回所有自定义字段的值，是决策前的重要参考。

#### 意图 2：智能打单 (Create Issue)
- **剧本**：用户要求创建一个 Bug、Feature 等。
- **两阶段机制**：
  1. **获取 Schema**：执行 `python scripts_py/schema.py --project "<KEY>" --issuetype "<Type>"`。
  2. **校验与提交**：对比 Schema 中的 `required_fields`，缺项则反问。集齐信息后调用：
     `python scripts_py/create.py --payload '{"fields":{...}}'`
- **💡 重要：Jira 7.x 人员字段请直接使用 `{"name": "username"}` 格式。**

#### 意图 3：工单内容更新 (Update Fields)
- **脚本**：`python scripts_py/update.py --issue "<KEY>" --payload '{"fields":{...}}'`

#### 意图 3.5：工单状态流转 (Transition Workflow)
- **脚本**：
  1. 列出动作：`python scripts_py/transition.py --issue "<KEY>" --list`
  2. 执行流转：`python scripts_py/transition.py --issue "<KEY>" --id "<TransitionID>"`
- **剧本**：用户说"把单子关了"、"开始处理这个 Bug"。

#### 意图 4：工单删除 (Delete Issue)
- **脚本**：`python scripts_py/delete.py --issue "<KEY>"`
- **风控**：在执行前，**必须**显式反问用户："你确定要永久删除工单 {KEY} 吗？此操作不可撤销。"。得到肯定答复（如"是的"、"确定"）后方可调用。

## 大模型避坑与自愈指南 (LLM Gotchas & Auto-Healing)

### 0. 记忆库分级读取策略
`MEMORY.md` 是你的渐进式大脑。
- **创建/更新前**：必读 §1 别名映射、§3 JSON 模板、§4 项目快照。
- **遇到 400 错后**：必读 §2 踩坑复盘，寻找 7.5.2 特有的字段报错解法。

### 1. 记忆库的自我进化
你被授权且**强制要求**在操作结束后更新 `MEMORY.md`：
- 发现新的自定义字段含义 -> 写入 §1。
- 攻克了一个变态校验字段 -> 写入 §3。
- 掌握了某个项目的工作流路径 -> 写入 §6。

### 2. 字段映射建议 (Jira 7.x 特色)
- **人员**：Jira 7.5.2 主要使用 `name`（登录名）进行映射。如果不知道 `name`，请先通过 `users_dict.py --keyword <姓名>` 查找。
- **日期**：通常格式为 `YYYY-MM-DD`。
- **级联/下拉**：优先参考 `schema.py` 返回的 `allowedValues` 信息。

### 3. 不要伪造
永远不要伪造 Transition ID 或字段名。如果不确定，先调用对应的查询/元数据脚本（`get_issue`, `schema`, `transition --list`）。
