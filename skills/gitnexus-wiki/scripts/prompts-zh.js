/**
 * LLM Prompt Templates for Wiki Generation (中文版)
 *
 * 所有提示词生成中文文档
 * Templates use {{PLACEHOLDER}} substitution.
 */
// ─── Grouping Prompt ──────────────────────────────────────────────────
export const GROUPING_SYSTEM_PROMPT = `你是一个文档架构师。根据源文件列表及其导出符号，将它们分组为逻辑文档模块。

规则：
- 每个模块应代表一个内聚的功能、层或领域
- 每个文件必须恰好出现在一个模块中
- 模块名称应易于理解（例如："认证"、"数据库层"、"API 路由"）
- 对于典型项目，目标为 5-15 个模块。小项目更少，大项目更多
- 按功能分组，而不仅仅是按文件类型或目录结构
- 不要为测试、配置或非源文件创建模块`;
export const GROUPING_USER_PROMPT = `将这些源文件分组为文档模块。

**文件及其导出：**
{{FILE_LIST}}

**目录结构：**
{{DIRECTORY_TREE}}

仅响应 JSON 对象，将模块名称映射到文件路径数组。不要 markdown，不要解释。
示例格式：
{
  "认证": ["src/auth/login.ts", "src/auth/session.ts"],
  "数据库": ["src/db/connection.ts", "src/db/models.ts"]
}`;
// ─── Leaf Module Prompt ───────────────────────────────────────────────
export const MODULE_SYSTEM_PROMPT = `你是一个技术文档编写者。为代码模块编写清晰、面向开发者的文档。

规则：
- 引用实际的函数名、类名和代码模式 — 不要发明 API
- 使用调用图和执行流数据以确保准确性，但不要机械地列出每条边
- 仅在真正有助于理解时包含 Mermaid 图。保持小规模（最多 5-10 个节点）
- 以最适合该模块的方式构建文档 — 没有强制格式
- 为需要理解和贡献此代码的开发者编写`;
export const MODULE_USER_PROMPT = `为 **{{MODULE_NAME}}** 模块编写文档。

## 源代码

{{SOURCE_CODE}}

## 调用图与执行流（参考以确保准确性）

内部调用：{{INTRA_CALLS}}
外部调用：{{OUTGOING_CALLS}}
传入调用：{{INCOMING_CALLS}}
执行流：{{PROCESSES}}

---

为此模块编写全面的文档。涵盖其目的、工作原理、关键组件以及如何连接到代码库的其余部分。使用最适合该模块的结构 — 你决定章节和标题。仅在真正阐明架构时包含 Mermaid 图。`;
// ─── Parent Module Prompt ─────────────────────────────────────────────
export const PARENT_SYSTEM_PROMPT = `你是一个技术文档编写者。为包含子模块的模块编写摘要页面。综合子模块的文档 — 不要重新阅读源代码。

规则：
- 引用子模块中的实际组件
- 专注于子模块如何协同工作，而不是重复它们的单独文档
- 保持简洁 — 读者可以点击进入子页面查看详细信息
- 仅在真正阐明子模块关系时包含 Mermaid 图`;
export const PARENT_USER_PROMPT = `为 **{{MODULE_NAME}}** 模块编写文档，该模块包含以下子模块：

{{CHILDREN_DOCS}}

跨模块调用：{{CROSS_MODULE_CALLS}}
共享执行流：{{CROSS_PROCESSES}}

---

编写此模块组的简洁概述。解释其目的、子模块如何协同工作以及跨越它们的关键工作流。链接到子模块页面（例如 \`[子模块名称](sub-module-slug.md)\`）而不是重复其内容。使用最适合的结构。`;
// ─── Overview Prompt ──────────────────────────────────────────────────
export const OVERVIEW_SYSTEM_PROMPT = `你是一个技术文档编写者。为代码库编写顶级概述页面。这是新开发者看到的第一页。

规则：
- 清晰且友好 — 这是整个代码库的入口点
- 引用实际的模块名称，以便读者可以导航到其文档
- 包含仅显示最重要模块及其关系的高级 Mermaid 架构图（最多 10 个节点）。新开发人员应在 10 秒内掌握
- 不要创建模块索引表或列出每个模块的描述 — 只是在文本中自然链接到模块页面
- 使用跨模块边和执行流数据以确保准确性，但不要原始转储它们`;
export const OVERVIEW_USER_PROMPT = `为此代码库的 wiki 编写概述页面。

## 项目信息

{{PROJECT_INFO}}

## 模块摘要

{{MODULE_SUMMARIES}}

## 参考数据（为确保准确性 — 不要逐字复制）

跨模块调用边：{{MODULE_EDGES}}
关键系统流：{{TOP_PROCESSES}}

---

编写此项目的清晰概述：它的作用、架构方式以及关键端到端流。包含简单的 Mermaid 架构图（最多 10 个节点，仅大图）。在文本中自然链接到模块页面（例如 \`[模块名称](module-slug.md)\`），而不是在表格中列出它们。如果提供了项目配置，包含简短的设置说明。以最适合的方式构建页面。`;
// ─── Template Substitution Helper ─────────────────────────────────────
/**
 * 替换模板字符串中的 {{PLACEHOLDER}} 标记。
 */
export function fillTemplate(template, vars) {
    let result = template;
    for (const [key, value] of Object.entries(vars)) {
        result = result.replaceAll(`{{${key}}}`, value);
    }
    return result;
}
// ─── Formatting Helpers ───────────────────────────────────────────────
/**
 * 为分组提示格式化文件列表。
 */
export function formatFileListForGrouping(files) {
    return files
        .map(f => {
            const exports = f.symbols.length > 0
            ? f.symbols.map(s => `${s.name} (${s.type})`).join('、')
            : '无导出';
            return `- ${f.filePath}: ${exports}`;
        })
        .join('\n');
}
/**
 * 从文件路径构建目录树字符串。
 */
export function formatDirectoryTree(filePaths) {
    const dirs = new Set();
    for (const fp of filePaths) {
        const parts = fp.replace(/\\/g, '/').split('/');
        for (let i = 1; i < parts.length; i++) {
            dirs.add(parts.slice(0, i).join('/'));
        }
    }
    const sorted = Array.from(dirs).sort();
    if (sorted.length === 0)
        return '(扁平结构)';
    return sorted.slice(0, 50).join('\n') + (sorted.length > 50 ? `\n... 以及另外 ${sorted.length - 50} 个目录` : '');
}
/**
 * 将调用边格式化为可读文本。
 */
export function formatCallEdges(edges) {
    if (edges.length === 0)
        return '无';
    return edges
        .slice(0, 30)
        .map(e => `${e.fromName} (${shortPath(e.fromFile)}) → ${e.toName} (${shortPath(e.toFile)})`)
        .join('\n');
}
/**
 * 将过程跟踪格式化为可读文本。
 */
export function formatProcesses(processes) {
    if (processes.length === 0)
        return '未检测到此模块的执行流。';
    return processes
        .map(p => {
            const stepsText = p.steps
                .map(s => `  ${s.step}. ${s.name} (${shortPath(s.filePath)})`)
                .join('\n');
            return `**${p.label}** (${p.type}):\n${stepsText}`;
        })
        .join('\n\n');
}
/**
 * 缩短文件路径以提高可读性。
 */
function shortPath(fp) {
    const parts = fp.replace(/\\/g, '/').split('/');
    return parts.length > 3 ? parts.slice(-3).join('/') : fp;
}
