---
name: codebase-memory-mcp-setup
description: "跨平台安装、迁移、配置、增强和维护 Codebase Memory MCP（CBM）。当用户要求从官方仓库安装或更新 codebase-memory-mcp、自定义 CBM_CACHE_DIR/CBM_RUNTIME_DIR、为 Codex 或 Claude Code 配置 MCP 与 graph-first 主导模式、启用 auto_index/auto_watch、建立或检查索引，以及排查 PATH、ACL、daemon、Hook 或大仓库问题时使用。"
---

# Codebase Memory MCP 配置与维护

所有说明、执行回显和交付使用简体中文。命令、配置键和工具名保留英文。

## 核心约束

1. 只从官方仓库 `https://github.com/DeusData/codebase-memory-mcp` 或其 GitHub Releases 获取安装器和二进制。
2. 先识别操作系统、Shell、CPU 架构、目标客户端和现有安装，再选择对应流程。Windows 优先 PowerShell 7；macOS/Linux 使用 POSIX shell。
3. 把安装目录、缓存目录和 runtime 父目录视为三个独立参数。不得把当前机器的盘符、用户名、SID 或项目路径写入 Skill、文档或模板。
4. 修改 Agent 配置前先备份；首次安装先用官方安装器的 `--skip-config` 安装二进制，再用原生命令 `install --skip-binary --dry-run --clients=claude,codex` 预览精确变更。
5. 不删除或放宽 Codex 沙箱 ACL，不绕过 CBM 的私有目录校验。出现权限错误时修复目标目录所有权/DACL/ACL，或换到当前用户独占的目录。
6. 不承诺模型每次都调用 MCP。主导模式依靠 MCP `initialize.instructions`、Skill、Agent profile、项目指令和 Hooks 叠加提高调用优先级；最终工具选择仍由 Agent 决定。
7. `auto_index=true` 只控制首次连接时自动建索引，不等于强制调用 MCP。`auto_watch=true` 只维护已索引、已连接会话中的 Git 项目。
8. 对外部下载、配置写入、索引创建、更新、卸载等有状态操作，必须符合用户授权范围。未经授权不得批量扫描或索引用户未指定的目录。

## 执行路由

### 安装、迁移或客户端增强

完整读取 [installation.md](references/installation.md)，按以下顺序执行：

1. 收集 `CBM_INSTALL_DIR`、`CBM_CACHE_DIR`、可选 `CBM_RUNTIME_DIR` 和目标客户端。
2. 检查现有二进制、版本、进程、配置和目录权限。
3. 备份目标配置，下载并检查官方安装器。
4. 安装二进制，运行配置 dry-run，再只配置用户指定的客户端。
5. 持久化环境变量，开启 `auto_index`，验证 MCP、Hook 和索引状态。

### 更新、自动监听或索引健康

完整读取 [operations.md](references/operations.md)。更新前关闭或协调现有 Agent 会话；更新后重新运行客户端配置 dry-run，并复核环境变量转发、Hooks 和索引兼容性。

### 故障排查

完整读取 [troubleshooting.md](references/troubleshooting.md)。优先根据错误文本定位，不使用“禁用安全检查”“删除未知 ACL”“全盘授权”等破坏性做法。

## Graph-first 主导协议

安装器检测到 Codex 或 Claude Code 后，会配置 MCP、共享 `codebase-memory` Skill、Scout/Verify/Auditor 分层 Agent profile 和生命周期增强：

- Codex：MCP 配置、全局 `AGENTS.md` 托管块、Skill、分层 Agent profile、`SessionStart` 与 `SubagentStart` 动态上下文。
- Claude Code：MCP 配置、Skill、分层 Agent profile、`SessionStart`/`SubagentStart` 提醒，以及非阻塞的 Grep/Glob/Read 覆盖增强。
- MCP 初始化说明：要求结构探索优先使用 `search_graph`，调用链使用 `trace_path`，精确源码使用 `get_code_snippet`，并用 `check_index_coverage` 验证证据覆盖。

如用户要求项目级强化，可在得到写入授权后，向该项目的 `AGENTS.md` 或 `CLAUDE.md` 添加简短、可管理的 graph-first 规则。不得覆盖原文件；不得同时保留互相冲突的 GitNexus 或其他图谱工具强制规则。

## 完成标准

- `codebase-memory-mcp --version` 可运行，且命令来自预期安装目录。
- `codebase-memory-mcp config get auto_index` 返回 `true`。
- `codebase-memory-mcp config get auto_watch` 返回预期值；建议显式设为 `true`。
- Codex 和 Claude Code 的实际配置中存在 CBM MCP，且所有启动方式都能获得一致的 `CBM_CACHE_DIR` 与 `CBM_RUNTIME_DIR`。
- `codebase-memory-mcp cli list_projects` 可运行；指定项目时，`index_status` 和 `check_index_coverage` 能返回可信结果。
- Agent 重启后能看到 MCP 工具；Codex 非托管 Hooks 已在 `/hooks` 中完成用户信任。
- 没有将本机专属路径、凭据、SID 或隐私信息写入 Skill 仓库。

## 官方事实边界

- 默认 cache 为用户目录下的 `.cache/codebase-memory-mcp`。
- 默认 runtime 父目录：Windows 为 Local AppData，macOS 为 `/private/tmp`，其他 POSIX 系统为 `/tmp`。
- `auto_index` 默认 `false`，`auto_index_limit` 默认 `50000`，`auto_watch` 默认 `true`。
- `CBM_CACHE_DIR` 不会移动 daemon rendezvous；只有 `CBM_RUNTIME_DIR` 控制 runtime 父目录。
- 当前官方版本不会自行联网检查更新。`codebase-memory-mcp update` 只验证参数并打印安装目录旁官方安装脚本的精确更新命令。
- 官方安装器校验 release checksum，并用托管块/结构化编辑更新配置；仍应备份并做 dry-run，因为检测到的客户端和现有自定义配置会影响实际变更。
