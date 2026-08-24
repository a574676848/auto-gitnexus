# 安装与运行故障排查

## 1. 私有目录或 ACL 校验失败

常见信息包括：

- `secure daemon endpoint could not be created`
- `acl-grants-cross-account-mutation`
- activation transaction、cache 或 runtime ancestry 安全检查失败

CBM 会检查 runtime rendezvous 的每级祖先目录和 cache/安装激活目录。`CBM_RUNTIME_DIR` 只改变位置，不会放宽校验；源码没有安全绕过开关。

处理原则：

1. 用只读命令检查规范化后的目标、owner、权限和继承 ACL/DACL。
2. 优先新建当前用户独占的专用目录。
3. POSIX 确保目录由当前用户拥有，去掉扩展 allow ACL，并收紧至 `0700` 或符合组织策略的 `0750`。
4. Windows 确保 Owner 为当前用户，关闭不必要继承，并移除授予其他身份修改、删除、改 ACL 或改 Owner 的 ACE。
5. 只修改已确认属于 CBM 的专用目录。不得删除 Codex 沙箱组所需 ACL，也不得对用户目录、系统目录或整块磁盘递归重写权限。

若默认 runtime 祖先不安全，设置一个私有 `CBM_RUNTIME_DIR`；若默认 runtime 正常，保持默认更简单。所有需要共享 daemon 的进程必须看到同一 runtime 值。

## 2. MCP 多次 `Transport closed`，CLI 同时报用户目录 DACL 错误

这通常是同一个根因的两种表现：

- 手动 CLI 回退到默认用户目录后，私有目录安全检查直接输出 DACL/ACL 错误并以非零状态退出。
- MCP 子进程在返回 JSON-RPC `initialize` 响应前因同一检查退出，客户端只能报告 `Transport closed`；重试只会重复失败。

按以下顺序检查：

1. 在启动 Codex、Claude Code 或 IDE 的同一环境中读取 `CBM_CACHE_DIR` 和 `CBM_RUNTIME_DIR`，确认没有回退到默认用户目录。
2. Windows 用 `[Environment]::GetEnvironmentVariable('<name>', 'User')` 检查当前用户永久值；POSIX 检查实际登录/交互 shell 会加载的用户启动文件。只存在于旧终端的 `$env:` 或临时 `export` 不足以修复。
3. 检查主 MCP entry 的环境变量转发配置，同时检查 Scout/Verify/Auditor 等 Agent profile。profile 未写固定 `env` 时，其子进程依赖 Codex 宿主继承当前用户环境。
4. 完全退出并重新启动 Codex、终端、IDE 和其他宿主，再在未手工设置临时变量的新终端中运行 `codebase-memory-mcp cli list_projects`。
5. CLI 成功后再验证 MCP `initialize`。若仍失败，读取 daemon 日志并检查配置指向的专用 cache/runtime 目录 ACL。

不要删除 Codex 沙箱 ACL、递归改写用户目录 DACL，或寻找关闭 CBM 安全校验的开关。这些操作会扩大权限风险，而且不能解决不同进程环境不一致的问题。

## 3. 安装器临时目录继承了不安全 DACL

较新官方 Windows 安装器会为随机 staging 目录设置 owner-only DACL。仍失败时：

1. 确认安装器确实来自官方 main 或 release，并记录版本。
2. 检查 staging、安装目标和 cache/runtime，判断错误指向哪一层。
3. 在当前用户私有目录下载官方 release 与 `checksums.txt`，验证 SHA-256 后运行候选二进制的原生 `install --dir`。
4. 不跳过 checksum，不执行来源不明的旧安装器，不通过全盘 ACL 修改解决。

## 4. 自定义 cache 生效，但 runtime 未移动

这是预期行为：

- `CBM_CACHE_DIR` 控制索引、运行配置、UI 配置和日志。
- `CBM_RUNTIME_DIR` 控制 daemon rendezvous 父目录。

只想把大体积索引移到其他卷时，仅设置 `CBM_CACHE_DIR`，让 runtime 保持平台默认即可。删除旧 `CBM_RUNTIME_DIR` 前先关闭 Agent 会话，并确认该环境变量不是其他流程所需。

## 5. CLI 与 Agent 看见不同 cache 或 daemon

症状包括 MCP 初始化后工具消失、daemon handshake 冲突、CLI 有项目但 Agent 列表为空。

检查：

1. `Get-Command`/`command -v` 是否指向同一版本。
2. CLI、Codex、Claude Code 的父进程是否拥有同一 `CBM_CACHE_DIR` 和 `CBM_RUNTIME_DIR`。
3. Codex MCP entry 是否保留环境变量转发列表。
4. 是否在改变变量前关闭了所有 daemon-backed 会话。

CBM 每个账户同一时间只允许一个 canonical cache root。切换 cache 前关闭全部会话；不要同时运行指向两个 cache root 的 Agent。

## 6. 安装或更新后自定义配置变化

当前安装器使用托管块和结构化配置编辑，不应覆盖无关用户内容，但会刷新 CBM 自己管理的 MCP entry、Skill、Agent profile 和 Hooks。

因此每次执行前：

- 运行 `install --skip-binary --clients=claude,codex --dry-run`；
- 备份目标文件；
- 执行后对比配置；
- 复核 cache/runtime 环境转发。

如果 Hook 脚本已被用户修改，官方安装器会 fail-closed，拒绝把它当作自己的文件重写，并保留现有 Hook entry。不要强行覆盖；先比较内容，再决定恢复官方版本还是保留用户版本。

## 7. Codex Hook 没有触发

- 在 Codex 中打开 `/hooks`，检查非托管 Hook 是否需要信任。
- Hook 定义变化后重新检查信任。
- 确认 `hooks.json` 与 `config.toml` 没有同时维护同一 Hook；官方安装器会选择已有 `hooks.json`，避免双重注册。
- 动态上下文需要运行中的 CBM daemon/MCP session。服务不可用时 Hook 应跳过增强，不应阻断任务。

## 8. Claude Code 增强未触发

- 检查实际 `CLAUDE_CONFIG_DIR`，不要只看默认目录。
- 检查用户级 `.claude.json` 中 MCP entry、配置目录的 `settings.json` 和 hooks 子目录。
- `SessionStart`、`SubagentStart`、PreToolUse/PostToolUse 都是非阻塞增强；未触发不代表索引不存在。
- 从具有正确 cache/runtime 环境的终端启动 Claude Code，排除 GUI 环境变量未刷新。

## 9. `auto_index=true` 但没有索引

依次检查：

1. 项目是否通过 MCP session 提供了有效 repo root。
2. 项目文件数是否超过 `auto_index_limit`；默认上限为 `50000`。
3. 项目根是否为 CBM 永久拒绝的过宽或敏感目录。
4. 后台索引是否仍进行中，或 daemon 日志是否记录失败。
5. 使用显式 `index_repository` 验证是自动触发问题还是索引器问题。

`auto_index` 不会使 Agent 主动调用 MCP，也不会批量扫描磁盘上的所有项目。

## 10. `auto_watch=true` 但索引不新鲜

- watcher 只注册已索引并连接到会话的 Git 项目。
- 首次 poll 只建立 baseline；HEAD 或 working tree 后续变化才触发重建。
- 非 Git 项目不会持续监听。
- watcher 是后台轮询，关键任务前应调用 `detect_changes`、`index_status` 与 `check_index_coverage`。
- 纯 CLI 命令不启动共享 daemon/watchers。

## 11. PATH 指向旧安装

```bash
command -v -a codebase-memory-mcp
```

```powershell
Get-Command codebase-memory-mcp -All | Select-Object Source, Version
```

使用预期二进制绝对路径完成修复，再调整用户 PATH。不要在确认前删除其他安装；包管理器安装和 native 安装可能并存。

## 12. 更新或卸载被活动会话阻塞

执行 `codebase-memory-mcp daemon status` 查持有者，正常关闭 Codex、Claude Code、编辑器和临时索引命令后重试。不要强杀不相关进程。

卸载前明确选择是否保留 cache。卸载 Agent 集成和卸载二进制不等于删除 SQLite 索引；cache 是用户数据，除非用户明确要求，否则保留。
