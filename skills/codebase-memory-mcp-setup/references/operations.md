# 更新、监听与索引健康

## 1. 日常状态检查

```bash
codebase-memory-mcp --version
codebase-memory-mcp daemon status
codebase-memory-mcp config list
codebase-memory-mcp cli list_projects
```

对指定项目使用 `list_projects` 返回的 `name`：

```bash
codebase-memory-mcp cli index_status --project "$CBM_PROJECT_NAME"
codebase-memory-mcp cli detect_changes --project "$CBM_PROJECT_NAME"
```

Agent 在引用路径形成后应批量调用 MCP `check_index_coverage`。任何 missed range、未解析文件或索引模式不足都必须用源文件读取/文本搜索补证，不能把图谱未返回结果直接解释为“代码中不存在”。

## 2. 自动索引与自动监听的准确语义

- `auto_index=true`：MCP session 获得项目上下文时，如果该项目尚无数据库且文件数不超过 `auto_index_limit`，后台建立完整索引。
- 已存在索引：不会因 `auto_index` 再做首次索引，而是根据 `auto_watch` 注册 watcher。
- `auto_watch=true`：默认开启。监听已注册 Git 项目的 HEAD 变化和工作区 dirty 状态，并触发重建。
- watcher 只存在于 daemon-backed 会话生命周期中。纯 `cli` 命令不会启动或连接共享 daemon，也不会留下 watcher。
- 非 Git 项目不会由 Git watcher 持续维护，应显式重建。
- watcher 采用自适应轮询，不是提交后立即同步的强一致机制。关键分析前仍需检查 `index_status`、`detect_changes` 和覆盖率。

推荐显式配置：

```bash
codebase-memory-mcp config set auto_index true
codebase-memory-mcp config set auto_watch true
```

## 3. 显式建立或重建索引

自动索引被文件上限跳过、项目非 Git、索引损坏或更新说明要求重建时，使用用户明确授权的项目根目录：

```bash
codebase-memory-mcp cli --progress index_repository \
  --repo-path "$CBM_REPOSITORY_ROOT"
```

不要索引文件系统根、盘符根、用户主目录、系统目录或凭据目录。CBM 会拒绝这些范围；不要尝试绕过。

索引完成后：

1. 用 `list_projects` 取得真实项目名。
2. 调用 `index_status` 确认完成且非 degraded。
3. 对任务涉及路径调用 `check_index_coverage`。
4. 用一个已知符号执行 `search_graph`，再用 `get_code_snippet` 验证精确源码。

## 4. 官方更新流程

当前 CBM 不在后台联网检查更新。获取更新信息后先执行：

```bash
codebase-memory-mcp update
```

该命令不会自行下载更新，而是打印安装目录旁 `install.sh` 或 `install.ps1` 的精确命令。更新时：

1. 记录当前版本、安装目录、cache/runtime 变量和 `config list` 输出。
2. 备份 Codex 与 Claude Code 配置。
3. 关闭所有使用 CBM 的 Agent 会话；用 `daemon status` 检查残留持有者。
4. 执行 `update` 打印的官方脚本命令。
5. 重启 Agent 会话。
6. 再运行 `install --skip-binary --clients=claude,codex --dry-run`，确认托管块、Hooks 和 MCP entry 无漂移。
7. 复核 `auto_index`、`auto_watch`、环境变量和已有项目状态。

安装器会进行 checksum 校验和协调式激活。Windows 上必须由安装脚本替换正在使用的 executable；不要手动覆盖运行中的二进制。

若通过 npm 或 pip 安装，应使用同一包管理器更新，并确认它实际解析到的 runtime 版本。不要把包管理器安装与 native 安装混用后假设 PATH 顺序正确。

## 5. 更新后是否重建索引

默认先检查，不无条件删除 cache：

- 版本说明明确提到索引格式、解析器、边类型、语义边或 coverage 能力变化时，重建相关项目。
- `index_status` 报错、degraded、版本不兼容或查询结果明显缺失时，重建。
- 仅 Agent 配置、Hook 或安装器变化且现有索引健康时，不需要重建。

禁止把整个 cache 目录当作普通临时文件删除。需要移除单个项目时优先使用 MCP/CLI `delete_project`，并在执行前确认项目名。

## 6. 配置漂移检查

每次安装或更新后检查：

- 当前命令路径与预期安装目录一致，PATH 中无旧副本抢占。
- Codex MCP entry 仍含 `env_vars = ["CBM_CACHE_DIR", "CBM_RUNTIME_DIR"]`。
- 启动 Codex、Claude Code 和 CLI 的环境中，cache/runtime 值一致。
- 官方托管块存在且没有重复；用户自定义内容仍保留。
- Codex `/hooks` 信任状态有效；Claude Hooks 没有被第三方配置覆盖。
- daemon 日志位于 `${CBM_CACHE_DIR}/logs`，错误排查不依赖 stdout，因为 MCP stdout 保留给 JSON-RPC。
