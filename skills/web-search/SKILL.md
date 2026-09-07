---
name: web-search
description: 四路并行 web 搜索与页面抓取技能（Bing RSS / AnySearch / TinyFish / Tavily），一次调用同时查询四个搜索引擎，跨源去重并按"多源共识"排序，默认输出 agent 最易读的 Markdown；支持新闻/学术论文垂直搜索、日期与新鲜度过滤、域名白黑名单、AI 直答、全文抓取。当用户或 Agent 需要搜索网络信息、查证事实、获取最新资讯、调研技术方案、抓取网页内容时触发。关键词：搜索、联网、查资料、web search、search the web、fact-check、调研、抓取网页。
version: 2.0.0
metadata:
  author: auto-devnexus
---

# 四路并行 Web 搜索 Skill (AI Agent 指南)

本 Skill 包含两个 CLI：

| 脚本 | 用途 |
|---|---|
| `scripts/web_search.py` | 四路并行搜索 → 去重 → 共识排序 → **Markdown（默认）或 JSON** |
| `scripts/web_fetch.py` | 抓取任意 URL 全文，转干净 Markdown/HTML（TinyFish Fetch API） |

核心价值：**多源共识排序** —— 被 2+ 引擎同时返回的 URL 置顶（`***-` 星级标注），单源噪声自动沉底；**默认输出 Markdown**，Agent 直接阅读，无需先解析 JSON。

## 何时使用

- 联网获取任何当前信息（文档、新闻、技术方案、事实核查、学术调研）
- 用户说"搜一下"、"查查"、"帮我调研"、"最新版本是什么"
- 需要比单一引擎更可靠、覆盖面更广的搜索结果
- 需要网页全文（搜索摘要不够时），用 `web_fetch.py`

**优先级约定**：本 Skill 是本仓库联网查询的首选入口。部分引擎不可用时用剩余引擎继续；全部不可用才回退其他手段。

## 一、搜索：web_search.py

```bash
python <skill_dir>/scripts/web_search.py "<query>" [选项]
```

**输出契约**：stdout 输出 **Markdown（默认，Agent 直接阅读）**；加 `--json` 输出机器可读 JSON。stderr 输出一行统计（`--quiet` 关闭）。解析 stdout，忽略 stderr。

### 默认 Markdown 输出（Agent 直接消费）

````markdown
# Web Search: <query>
*5 results | 3000ms | 4/4 engines ok (bing+anysearch+tinyfish+tavily)*
> engine `tavily` failed: RuntimeError: ...     ← 仅失败时出现

## AI Answer (Tavily)          ← 仅 --answer 时出现
<一段 LLM 直接回答>

## Results
### 1. <标题>
- **URL**: https://...
- **Consensus**: ***- hit by anysearch+tavily+tinyfish (best rank 1 at tavily)
- **Score**: 0.902 | **Site**: ... | **Date**: 2 days ago    ← 有才显示
- **Authors**: A Vaswani, N Shazeer | **Citations**: 268152  ← 学术模式
> <摘要 snippet，最长 500 字符>
````

**星级语义**：`Consensus: ***-` = 4 个实心星中命中 3 个引擎；`****` 四引擎共识 = 最高置信；`*---` 单源 = 低置信，慎用。

### 场景速查表

| 场景 | 命令 |
|---|---|
| 通用搜索 | `web_search.py "query"`（默认四路全开） |
| 英文技术搜索 | `... --market en-US --location US --language en` |
| 中文搜索 | `... --market zh-CN --language zh` |
| 新闻 + AI 直答 | `... --news --answer --market en-US` |
| 学术论文 | `... --domain-type research_paper --pub-year-min 2022` |
| 近 24 小时新鲜度 | `... --recency-minutes 1440`（TinyFish）/ `--time-range day`（Tavily） |
| 日历日期范围 | `... --after-date 2026-09-01 --before-date 2026-09-07` |
| 域名白名单 | `... --include-domains "kubernetes.io,docs.python.org"` |
| 快速事实核查 | `... --providers anysearch,tavily --top 5` |
| 深调研 | `... --per-provider 15 --top 15 --depth advanced --purpose "..."` |
| 下一页结果 | `... --page 1`（TinyFish 翻页） |
| 机器可读输出 | `... --json` |

### 全部选项

| 选项 | 作用 | 生效引擎 |
|---|---|---|
| `--top N` / `--per-provider N` | 合并后条数（默认 10）/ 每路请求条数 | 全局 |
| `--providers a,b,...` | 引擎子集：`bing,anysearch,tinyfish,tavily` | 全局 |
| `--news` | 新闻模式 | Tavily topic / TinyFish domain_type |
| `--domain-type news\|research_paper` | TinyFish 垂直域（学术模式带 authors/venue/year/引用数/PDF 链接） | TinyFish |
| `--answer` | LLM 生成对 query 的直接回答 | Tavily |
| `--market xx-XX` | **Bing 必带**（en-US / zh-CN），否则区域污染 | Bing |
| `--location XX` / `--language xx` | 国家码 / 语言码 | TinyFish |
| `--time-range day\|week\|month\|year` | 相对新鲜度窗口 | Tavily |
| `--recency-minutes N` | 相对现在的新鲜度窗口（分钟） | TinyFish |
| `--after-date` / `--before-date` | 日历范围 YYYY-MM-DD（TinyFish after/before_date；Tavily start/end_date） | TinyFish+Tavily |
| `--pub-year-min` / `--pub-year-max` | 学术论文发表年份范围 | TinyFish |
| `--page N` | 翻页（0 基） | TinyFish |
| `--depth advanced` | 深度搜索（2 credits） | Tavily |
| `--include-domains` / `--exclude-domains` | 域名白/黑名单（逗号分隔） | TinyFish+Tavily |
| `--purpose "..."` | 搜索意图信号，提升结果质量 | TinyFish |
| `--json` | 机器可读 JSON 输出 | 全局 |
| `--raw` | 附每路原始结果（仅 JSON 模式有意义） | 全局 |
| `--timeout S` | 每路超时秒数（默认 20） | 全局 |

### 参数选择规则（Agent 必读）

1. **Bing 必须指定 `--market`**：不指定会得到随机语言污染结果（区域由出口 IP 决定）。
2. **查询语言与参数一致**：英文配 `--location US --language en`，中文配 `--language zh`。
3. **query 写关键词短语**，不要塞完整句子。
4. **学术调研**用 `--domain-type research_paper`（返回引用数/作者/venue，其他引擎正常补充 general 结果）。
5. **时效性信息**（新闻/版本）：加 `--news` 或 `--time-range week`；需要绝对时间段用 `--after-date/--before-date`。
6. **需要直接答案**（"X 是什么"类）：加 `--answer`，Tavily 生成一段 AI 直答。
7. **research_paper 模式下** `--recency-minutes/--after-date` 对 TinyFish 无效，年份过滤用 `--pub-year-*`。

## 二、抓取：web_fetch.py

```bash
python <skill_dir>/scripts/web_fetch.py <url...> [选项]
```

搜索摘要不够、需要页面全文时使用。**最多 10 个 URL/次，单 URL 失败不影响其他**。

```bash
# 基础抓取（Markdown，默认每页截断 20000 字符）
python scripts/web_fetch.py "https://example.com/post"

# 批量 + 意图信号
python scripts/web_fetch.py "https://a.com/1" "https://b.com/2" --purpose "比较两个库的定价"

# 只要正文某部分 / 剔除噪声
python scripts/web_fetch.py "https://example.com/blog" --include-selectors "article" --exclude-selectors ".comments,.ads"

# 强制实时抓取（不用缓存）/ 控制缓存新鲜度
python scripts/web_fetch.py "https://example.com" --ttl 0

# etag 条件请求：保存校验器后回放，页面未变则跳过正文（省 token）
python scripts/web_fetch.py "https://example.com" --save-validators   # 记下 etag
python scripts/web_fetch.py "https://example.com" --etag "<etag>"     # 未变时 not_modified

# HTML 格式 / 完整不截断 / JSON 输出
python scripts/web_fetch.py "https://example.com" --format html --max-chars 0 --json
```

| 选项 | 作用 |
|---|---|
| `--format markdown\|html` | 输出格式（默认 markdown） |
| `--purpose "..."` | 抓取意图信号 |
| `--ttl N` | 接受的缓存副本最大年龄（秒）；0 = 实时抓取 |
| `--include-selectors` / `--exclude-selectors` | CSS 选择器：只保留 / 先剔除 |
| `--etag` / `--if-modified-since` | 回放校验器（If-None-Match / If-Modified-Since） |
| `--save-validators` | 响应中带 etag/last_modified，供下次回放 |
| `--max-chars N` | 每页文本截断（默认 20000；0 = 不截断） |
| `--json` | 机器可读 JSON |

**返回字段**（Markdown 每页一节 / JSON pages[]）：`title`、`url`、`final_url`、`language`、`author`、`published_date`、`latency_ms`、`text`；失败 URL 单独列出（`error` + `status`）。

## 四路引擎与鉴权

| 引擎 | 接口 | 鉴权 | 特点 |
|---|---|---|---|
| bing | `GET bing.com/search?format=rss` | 无 key，免费 | RSS 2.0；count 不完全可靠 |
| anysearch | `POST api.anysearch.com/mcp` (JSON-RPC) | key 可选 | 实时搜索，快 |
| tinyfish | `GET api.search.tinyfish.ai` / `POST api.fetch.tinyfish.ai` | X-API-Key 必需 | 搜索垂直域 + 抓取全家桶 |
| tavily | `POST api.tavily.com/search` | Bearer 必需 | 相关性打分、AI 直答、advanced 深搜 |

密钥从 `<skill_dir>/.env` 读取（优先级：环境变量 > `.env` > `.env.qoder`），`.env` 已 git-ignore：

```
ANYSEARCH_API_KEY=    # 可选
TINYFISH_API_KEY=     # 必需（搜索垂直域 + web_fetch）
TAVILY_API_KEY=       # 必需（Tavily 路）
```

用户在聊天中发 key 时，提示其写入 `.env` 而非留在对话记录。

## 降级与错误处理

- **单路失败**：`providers[].status=error`（Markdown 顶部也会标注），其余引擎照常。质量不足可 `--providers` 子集重试。
- **TinyFish/Tavily 缺 key**：`--providers bing,anysearch` 继续（web_fetch 依赖 TinyFish key）。
- **Bing 区域污染**：必须带 `--market`；仍异常则跳过 Bing。
- **全部失败**：回退内置搜索工具并告知用户。
- **敏感查询**：query/URL 会发送到上述第三方服务，涉及密码、隐私数据不要使用。

## 实现说明

- 纯 Python 3 标准库（urllib + concurrent.futures），零第三方依赖，Windows/Linux 通用。
- **stdout/stderr 强制 UTF-8**（编码无关，管道/重定向不乱码）。
- 四路并发，总耗时 ≈ 最慢一路（2-4 秒）；去重键为 URL 规范化（去协议/www/尾斜杠/fragment）。
