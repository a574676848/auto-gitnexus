# 跨平台安装与客户端增强

## 1. 收集参数

不要替用户猜测专用数据盘或目录。至少确认或从当前上下文推导：

- `CBM_INSTALL_DIR`：二进制和官方安装脚本所在目录。
- `CBM_CACHE_DIR`：索引数据库、`_config.db`、UI 配置和 daemon 日志目录。通常占用空间最大。
- `CBM_RUNTIME_DIR`：daemon rendezvous 的父目录。仅在默认位置权限不合格或用户明确要求时自定义。
- 目标客户端：只配置 Codex、Claude Code，或用户明确指定的其他客户端。

目录必须归当前用户控制。POSIX 建议 owner-only `0700`；Windows 使用当前用户拥有、无跨账户写权限的专用目录。

## 2. 预检与备份

先执行只读检查：

```bash
command -v codebase-memory-mcp || true
codebase-memory-mcp --version 2>/dev/null || true
git --version
```

```powershell
Get-Command codebase-memory-mcp -ErrorAction SilentlyContinue
codebase-memory-mcp --version
git --version
```

备份真实存在的客户端配置。路径从环境和客户端自身解析，不拼接本机用户名：

- Codex：`$CODEX_HOME/config.toml`，未设置 `CODEX_HOME` 时通常位于用户目录的 `.codex`。
- Claude Code：`$CLAUDE_CONFIG_DIR/settings.json`，以及用户目录下的 `.claude.json`；未设置时配置目录通常为 `.claude`。

备份文件名附加 UTC 时间戳。只复制文件，不复制整个 cache 索引目录。

## 3. 获取官方安装器

官方入口：

- 仓库：`https://github.com/DeusData/codebase-memory-mcp`
- POSIX 安装器：`https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh`
- Windows 安装器：`https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.ps1`

先下载到随机临时文件并人工或程序化检查来源、目标参数和下载域名，再执行。不要在安全敏感环境中直接把远端内容管道给 Shell。

运行安装器前，先在当前 Shell 注入已确认的目录，使安装激活、后续 CLI 和 Agent 使用同一 cache/runtime。保留平台默认 runtime 时不要设置 `CBM_RUNTIME_DIR`：

```bash
export CBM_INSTALL_DIR="<private-install-directory>"
export CBM_CACHE_DIR="<private-cache-directory>"
# 仅在明确需要自定义 runtime 时：
export CBM_RUNTIME_DIR="<private-runtime-parent>"
# 若保留平台默认 runtime，改为执行：unset CBM_RUNTIME_DIR
```

```powershell
$env:CBM_INSTALL_DIR = $ConfiguredInstallDir
$env:CBM_CACHE_DIR = $ConfiguredCacheDir
if ($ConfiguredRuntimeDir) {
    $env:CBM_RUNTIME_DIR = $ConfiguredRuntimeDir
} else {
    Remove-Item Env:CBM_RUNTIME_DIR -ErrorAction SilentlyContinue
}
```

### macOS / Linux

```bash
installer_file="$(mktemp)"
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh \
  -o "$installer_file"
less "$installer_file"
bash "$installer_file" --dir="$CBM_INSTALL_DIR" --skip-config
rm -f "$installer_file"
```

官方 Linux 安装器会选择 portable 静态构建，避免旧版 glibc 不兼容；安装器会下载 `checksums.txt` 并强制校验 SHA-256。

### Windows / PowerShell 7+

```powershell
$InstallerUri = 'https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.ps1'
$InstallerFile = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName() + '.ps1')
Invoke-WebRequest -Uri $InstallerUri -OutFile $InstallerFile
Get-Content -LiteralPath $InstallerFile
& $InstallerFile "--dir=$env:CBM_INSTALL_DIR" '--skip-config'
Remove-Item -LiteralPath $InstallerFile
```

若执行策略阻止已下载脚本，可对该临时文件执行 `Unblock-File -LiteralPath $InstallerFile`，或在当前进程范围使用经组织允许的执行策略；不要永久降低整机策略。

## 4. 持久化目录配置

### POSIX shell

在用户实际使用的 shell 启动文件中设置，并重启所有 Agent 会话：

```bash
export CBM_CACHE_DIR="<private-cache-directory>"
# 仅在需要自定义 runtime 时设置：
export CBM_RUNTIME_DIR="<private-runtime-parent>"
```

如果保留默认 runtime，完全不要设置 `CBM_RUNTIME_DIR`。确保 CLI、Codex、Claude Code 从同一环境启动。

### Windows

当前会话：

```powershell
$env:CBM_CACHE_DIR = $ConfiguredCacheDir
if ($ConfiguredRuntimeDir) {
    $env:CBM_RUNTIME_DIR = $ConfiguredRuntimeDir
}
```

持久化到当前用户环境：

```powershell
[Environment]::SetEnvironmentVariable('CBM_CACHE_DIR', $ConfiguredCacheDir, 'User')
if ($ConfiguredRuntimeDir) {
    [Environment]::SetEnvironmentVariable('CBM_RUNTIME_DIR', $ConfiguredRuntimeDir, 'User')
}
```

保留默认 runtime 时，应删除旧的用户级 `CBM_RUNTIME_DIR`，但执行前必须确认该值确由本次 CBM 配置使用：

```powershell
[Environment]::SetEnvironmentVariable('CBM_RUNTIME_DIR', $null, 'User')
```

环境变化不会注入已运行进程。关闭所有 daemon-backed Agent 会话后重新启动。

## 5. 预览并配置 Codex / Claude Code

使用刚安装的二进制绝对路径，避免 PATH 指向旧版本：

```bash
"$CBM_INSTALL_DIR/codebase-memory-mcp" install --skip-binary \
  --clients=claude,codex --dry-run
"$CBM_INSTALL_DIR/codebase-memory-mcp" install --skip-binary \
  --clients=claude,codex -y
```

```powershell
$CbmBinary = Join-Path $env:CBM_INSTALL_DIR 'codebase-memory-mcp.exe'
& $CbmBinary install --skip-binary --clients=claude,codex --dry-run
& $CbmBinary install --skip-binary --clients=claude,codex -y
```

`--dry-run` 会列出本机精确配置文件和 Hook 变更。不要直接使用无 `--clients` 的全客户端配置，除非用户明确要求配置所有检测到的客户端。

官方 Codex 配置会为 MCP entry 写入：

```toml
env_vars = ["CBM_CACHE_DIR", "CBM_RUNTIME_DIR"]
```

这表示“若父进程存在这些变量则转发”，不是写入目录值。因此仍需让启动 Codex 的进程获得持久化环境。Claude Code 同样应从具有一致变量的环境启动；如由 GUI 启动，确认 GUI 进程能读取用户环境。

## 6. 开启自动索引和监听

```bash
codebase-memory-mcp config set auto_index true
codebase-memory-mcp config set auto_watch true
codebase-memory-mcp config get auto_index
codebase-memory-mcp config get auto_watch
codebase-memory-mcp config get auto_index_limit
```

`auto_index_limit` 默认 `50000`。超过限制的项目不会自动索引；此时应由用户明确指定项目并调用 `index_repository`，或评估资源后调整限制。不要为了“自动成功”盲目提高上限。

## 7. 主导模式增强与验证

官方配置叠加以下机制：

1. MCP `initialize.instructions` 提供 graph-first 工具顺序。
2. 全局指令托管块和共享 Skill 提醒主 Agent 优先使用图谱。
3. Scout、Verify、Auditor profile 对快速探索、任务验证和边界审计分层。
4. Session/Subagent Hooks 注入动态上下文；Claude 还提供非阻塞搜索与读取覆盖增强。

Codex 的非托管 Hooks 需要在 `/hooks` 中由用户信任；Hook 定义变化后可能需要重新信任。Hook 的动态上下文依赖可用的 CBM daemon/MCP session，服务不可用时应 fail-open 并提示，而不是阻断工作。

需要项目级规则时，追加一个受管理的短块，表达以下语义即可：

```markdown
结构探索优先调用 Codebase Memory MCP：先用 search_graph 定位符号，
用 trace_path 分析调用关系，用 get_code_snippet 读取精确实现，并对引用路径调用
check_index_coverage。仅在查找字面量、配置、非代码文件或图谱覆盖不足时回退到文本搜索。
```

不得宣称这能绝对强制模型调用 MCP。

## 8. 首次验证

```bash
codebase-memory-mcp --version
codebase-memory-mcp config list
codebase-memory-mcp cli list_projects
```

随后重启 Codex/Claude Code，在一个用户授权的 Git 项目内确认：

- MCP 工具可见；
- 新项目在文件限制内会异步自动索引；
- `index_status` 最终显示完成；
- 对实际证据路径调用 `check_index_coverage` 不存在未覆盖范围，或已回退读取源码。
