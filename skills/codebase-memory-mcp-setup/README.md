# Codebase Memory MCP Setup Skill

用于指导 Codex、Claude Code 等 Agent 跨平台、安全地安装和维护 [Codebase Memory MCP](https://github.com/DeusData/codebase-memory-mcp)。

## 能力

- 从官方安装器和 GitHub Releases 安装 CBM，并校验来源与 checksum 流程。
- 分离配置二进制目录、索引 cache 和 daemon runtime，支持将大体积索引放到其他卷。
- 将目录配置持久化到当前用户环境，使主 Agent、分层 Agent profile 和手动 CLI 使用同一 cache/runtime。
- 为 Codex 与 Claude Code 安装 MCP、Skill、分层 Agent profile 和 Hooks。
- 开启 `auto_index` 与 `auto_watch`，并说明它们的真实边界。
- 维护版本、索引健康和 graph-first 工作流。
- 排查 Windows ACL、POSIX 权限、`Transport closed`、PATH、多版本、daemon、Hook 信任和大仓库限制。

## 使用方式

对 Agent 说明目标即可，例如：

```text
使用 $codebase-memory-mcp-setup 安装 CBM，把 cache 放到我指定的数据目录，
runtime 保持平台默认，并配置 Codex 和 Claude Code。
```

```text
使用 $codebase-memory-mcp-setup 检查 CBM 更新、自动监听和现有索引健康状态。
```

Skill 不包含本机盘符、用户名、SID 或项目路径。执行时由 Agent 从用户输入、环境变量和客户端配置解析实际目录。

## 目录结构

```text
codebase-memory-mcp-setup/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
└── references/
    ├── installation.md
    ├── operations.md
    └── troubleshooting.md
```

## 重要边界

- `auto_index=true` 不会强制 Agent 调用 MCP，也不会扫描磁盘上的所有仓库。
- `CBM_CACHE_DIR` 与 `CBM_RUNTIME_DIR` 是两个独立位置；只迁移大体积索引时无需迁移 runtime。
- Windows 只设置当前 PowerShell 的 `$env:` 不会覆盖新启动的 GUI、Agent profile 或 CLI；必须同时写入当前用户环境并完全重启宿主。
- CBM 私有目录安全校验没有绕过开关。应修复专用目录权限或更换目录，不能破坏系统或沙箱 ACL。
- 更新和卸载默认保留用户索引数据，删除 cache 必须由用户明确授权。

## 来源

- 官方仓库：<https://github.com/DeusData/codebase-memory-mcp>
- 官方配置说明：<https://github.com/DeusData/codebase-memory-mcp/blob/main/docs/CONFIGURATION.md>
- Codex MCP 配置说明：<https://learn.chatgpt.com/docs/extend/mcp>
