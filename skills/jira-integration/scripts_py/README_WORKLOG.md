# Jira 工时查询脚本 (worklog.py)

查询 Jira 工单工时信息的专用脚本，支持按用户、时间范围、用户 + 时间、工单四种查询模式。

## 快速开始

### 1. 按用户查询（默认最近 7 天）

```bash
python scripts_py/worklog.py --user "zhangbaogen" --workdir "<用户工作空间 tmp 路径>"
```

### 2. 按时间范围查询（所有用户）

```bash
python scripts_py/worklog.py --from "2026-03-01" --to "2026-03-31" --workdir "<用户工作空间 tmp 路径>"
```

### 3. 按用户 + 时间查询

```bash
python scripts_py/worklog.py --user "zhangbaogen" --from "2026-03-01" --to "2026-03-31" --workdir "<用户工作空间 tmp 路径>"
```

### 4. 按工单查询（所有工时）

```bash
python scripts_py/worklog.py --issue "PROJ-123" --workdir "<用户工作空间 tmp 路径>"
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--user` | 否 | 用户名（Jira login name） |
| `--from` | 否 | 开始日期（YYYY-MM-DD） |
| `--to` | 否 | 结束日期（YYYY-MM-DD） |
| `--issue` | 否 | 工单 KEY（如 PROJ-123） |
| `--max` | 否 | 最大返回工单数量（默认 100） |
| `--workdir` | **是** | 用户工作空间 tmp 路径（凭证存储位置） |

## 参数冲突规则

- `--issue` 不能与 `--user/--from/--to` 同时使用
- 其他参数可以自由组合

## 返回数据格式

### 成功响应

```json
{
  "success": true,
  "query": {
    "user": "zhangbaogen",
    "from": "2026-03-01",
    "to": "2026-03-13"
  },
  "summary": {
    "total_issues": 5,
    "total_worklog_count": 10,
    "total_worklog_seconds": 28800,
    "total_worklog_formatted": "8h"
  },
  "total_matches": 5,
  "returned_count": 10,
  "worklogs": [
    {
      "issue_key": "PROJ-123",
      "issue_summary": "Fix login bug",
      "time_spent_seconds": 3600,
      "time_spent": "1h",
      "comment": "Fixed the authentication issue",
      "started": "2026-03-10T14:00:00.000+0800",
      "created": "2026-03-10T14:05:00.000+0800",
      "author": "zhangbaogen",
      "link": "https://jira.example.com/browse/PROJ-123"
    }
  ]
}
```

### 错误响应

**缺少凭证**:
```json
{
  "success": false,
  "error_type": "MISSING_CREDENTIALS",
  "message": "缺少必要的配置信息（账号、Token 或 Jira 域名）..."
}
```

**参数冲突**:
```json
{
  "success": false,
  "error_type": "PARAMETER_CONFLICT",
  "message": "--issue 参数不能与 --user/--from/--to 同时使用..."
}
```

## 工时格式说明

脚本自动将秒数转换为人类可读格式：

| 秒数 | 显示格式 |
|------|----------|
| 30 | `30s` |
| 90 | `1m 30s` |
| 3600 | `1h` |
| 5400 | `1.5h` |
| 7260 | `2h 1m` |

## 技术实现

### JQL 查询逻辑

脚本使用以下 JQL 查询工单：

```jql
worklogAuthor = "username" AND worklogDate >= "from" AND worklogDate <= "to"
```

### API 调用

- 端点：`GET /rest/api/2/search`
- 字段：`fields=id,key,summary,worklog`
- 分页：支持 `maxResults` 参数（默认 100）

### 客户端二次过滤

由于 Jira 返回的每个 issue 可能包含所有工时记录（不仅限于 JQL 匹配的），脚本会在客户端进行二次过滤：

1. 按作者名称精确匹配
2. 按日期范围精确匹配

这确保了返回的工时记录 100% 符合查询条件。

## 常见用例

### 用例 1：生成周报

```bash
# 查询本周工时（假设周一是 2026-03-09）
python scripts_py/worklog.py --user "zhangbaogen" --from "2026-03-09" --to "2026-03-13" --workdir "C:\tmp\xxx"
```

### 用例 2：月度工时统计

```bash
# 查询 2026 年 3 月所有工时
python scripts_py/worklog.py --user "zhangbaogen" --from "2026-03-01" --to "2026-03-31" --workdir "C:\tmp\xxx"
```

### 用例 3：项目工时审计

```bash
# 查看某个项目的所有工时
python scripts_py/worklog.py --issue "PROJ-123" --max 500 --workdir "C:\tmp\xxx"
```

### 用例 4：团队工时查看

```bash
# 查看某一天所有团队成员的工时
python scripts_py/worklog.py --from "2026-03-13" --to "2026-03-13" --workdir "C:\tmp\xxx"
```

## 依赖

- Python 3.x
- utils.py（同一目录下的工具模块）
- Jira Server 7.5.2+（已验证兼容）

## 注意事项

1. **凭证管理**：首次使用需调用 `auth.py` 配置 Jira 凭证
2. **工作目录**：必须传入 `--workdir` 以隔离不同用户的凭证
3. **权限要求**：API 调用用户需要有查看对应项目和工单的权限
4. **性能考虑**：查询大范围时间可能返回大量数据，建议配合 `--max` 限制

## 相关文件

- `auth.py` - 凭证配置脚本
- `utils.py` - 通用工具函数
- `search.py` - 工单搜索脚本（worklog.py 复用了其 API 调用逻辑）
