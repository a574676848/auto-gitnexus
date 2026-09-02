# Stitch 语义化设计系统规范 (Stitch DESIGN.md Generator)

## 1. 规范目的与运行机制

本规范用于快速生成适配 **Google Stitch** 及各类 AI 前端编码 Agent 的 `DESIGN.md` 设计系统事实单一来源 (SSOT)。
Stitch 与 AI Agent 通过自然语言**“视觉意图描述”**结合具体的色值 Token、字阶规范与布局约束来准确生成高质量界面。

---

## 2. 标准 DESIGN.md 模板契约

生成的 `DESIGN.md` 必须严格包含以下七大核心章节：

```markdown
# Design System: [项目名称]

## 1. Visual Theme & Atmosphere (视觉基调与氛围)
- **氛围定性**：[如：克制的画廊空灵感，搭配富有张力的非对称布局与沉稳的弹簧动效。整体感：昂贵、精密、富有生命力。]
- **核心刻度设定**：Variance: [1-10] | Motion: [1-10] | Density: [1-10]

## 2. Color Palette & Roles (色彩角色与十六进制色值)
- **Canvas Background**: #[HEX] — 主画布底色（严禁纯黑 #000000）
- **Surface Elevation**: #[HEX] — 悬浮卡片与容器底色
- **Text Primary**: #[HEX] — 主标题与高对比正文（Zinc-950 / 炭黑深度）
- **Text Secondary**: #[HEX] — 次级描述与元数据
- **Structural Border**: rgba(..., ...) — 1px 结构发丝线
- **Brand Accent (单一受控)**: #[HEX] — 全局 CTA 与激活状态点睛色（饱和度 < 80%）
- **绝对严禁色**：严禁 AI 紫色渐变霓虹、严禁未受控的高饱和多色混杂。

## 3. Typography Rules (排版字阶规范)
- **Display**: [Geist / Satoshi / Cabinet Grotesk / PP Editorial New] — 紧致字距 (`-0.03em`)，行距压缩 (`1.1`)，桌面端严禁超过 3 行。
- **Body**: [同系 Sans 字体] — 行距宽松 (`1.6`)，最大行宽 `65ch`。
- **Mono**: [Geist Mono / JetBrains Mono] — 专用于代码、时间戳与高密数值。
- **字体禁令**：严禁无理由默认使用 Inter/Roboto/Arial，严禁在管理台使用衬线体。

## 4. Component Stylings (组件造型与交互)
- **Buttons**: 药丸形 (`rounded-full`) 或微圆角 (`rounded-lg`)，无外发光。内嵌独立图标圆圈，Active 态具备 `-translate-y-[1px]` 或 `scale-[0.98]` 物理下压反馈。
- **Cards**: 采用双层嵌套倒角 (`rounded-[2rem]` 外层 + 同心内层)，仅在需要表达层级时启用悬浮。
- **Inputs**: 标签置顶，报错在下，聚焦呈现品牌点睛色外圈 (`ring-2 ring-accent/30`)。
- **Loaders**: 骨架屏微光扫描（与组件轮廓 100% 同构），严禁圆形加载菊花。

## 5. Layout & Spatial Principles (布局与空间原则)
- **英雄区保障**：必须声明 `min-h-[100dvh]`，首屏文案精炼，CTA 无需滚动立即可见。
- **网格严密性**：Bento 特性网格必须应用 `grid-auto-flow: dense`，数学上零空白空洞。
- **排斥套路**：严禁千篇一律的三等分卡片行；段落间距必须保持大呼吸感 (`py-24` 至 `py-40`)。

## 6. Motion & Interaction Intent (动效与交互意图)
- **物理模型**：全栈采用弹簧物理（`stiffness: 100, damping: 20`），杜绝线性过渡。
- **常态微循环**：激活状态徽章呼吸微闪、搜索框光标微闪烁。
- **性能守卫**：仅动画化 `transform` 与 `opacity`，支持 `prefers-reduced-motion` 降级。

## 7. Anti-Patterns (严禁反模式清单)
- ❌ 严禁出现破折号 `—` 或 `–`
- ❌ 严禁 AI 假大空词汇 (Elevate, Seamless, Unleash, Next-Gen)
- ❌ 严禁使用 Div 拼接的假产品截图
- ❌ 严禁纯文本无图的伪极简
```
