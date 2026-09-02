# 视觉风格范式与设计系统映射库 (Styles & Archetypes)

## 1. 核心视觉风格范式 (Visual Archetypes)

在项目启动时，依据行业属性与品牌定位严格选择一种主视觉范式并贯穿始终：

### 1.1 Ethereal Glass (以太微光 / SaaS & AI)
- **基底与色彩**：深邃 OLED 纯黑背景 (`#050505` / `zinc-950`)，低饱和度环境径向辉光（如浅祖母绿、深靛蓝微晕）。
- **材质质感**：磨砂玻璃面板采用 `backdrop-blur-2xl bg-white/[0.03]`，边缘搭配 `1px solid rgba(255,255,255,0.08)` 细发丝线与内阴影高光。
- **排版推荐**：`Geist Sans` + `Geist Mono` 或 `Cabinet Grotesk`，字阶对比鲜明。

### 1.2 Utilitarian Minimalism (实用主义极简 / Workspace & Tools)
- **基底与色彩**：温暖骨白画布 (`#F7F6F3` 或 `#FFFFFF`)，碳墨文字 (`#111111`)，极浅结构细线 (`#EAEAEA`)。
- **点睛粉彩 (Spot Pastels)**：仅在 Tag、行内代码与微图标使用低饱和粉彩：
  - 淡红: `#FDEBEC` (字: `#9F2F2D`) | 淡蓝: `#E1F3FE` (字: `#1F6C9F`)
  - 淡绿: `#EDF3EC` (字: `#346538`) | 淡黄: `#FBF3DB` (字: `#956400`)
- **微交互元素**：实体按键效果 `<kbd>` (`bg-[#F7F6F3] border-[#EAEAEA] rounded-[4px]`)，极简无边框手风琴。

### 1.3 Swiss Industrial & Tactical Telemetry (瑞士工业粗野与战术遥测)
- **瑞士工业印刷 (Light)**：未漂白纸基 (`#F4F4F0`) + 炭黑字 (`#050505`) + 航空警戒红 (`#E61919`)。
- **战术遥测终端 (Dark)**：显像管熄灭暗底 (`#0A0A0A`) + 荧光白字 (`#EAEAEA`) + 局部遥测绿 (`#4AF626`)。
- **结构硬核**：绝对 90 度直角（`rounded-none`），刚性网格细线 (`gap-[1px] bg-neutral-800`)，ASCII 字符修饰 (`[ SYSTEM ACTIVE ]`, `>>>`)。

### 1.4 Editorial Luxury (高定杂志风 / Lifestyle & Fashion)
- **基底与色彩**：暖奶油色 (`#FDFBF7`) / 浅石灰 / 意式浓缩咖啡色。
- **排版与质感**：高辨识度现代衬线标题 (`PP Editorial New` / `Canela` / `Söhne Breit Kursiv`) 搭配无衬线正文。全局固定层 `0.03` 透明度纸张胶片微噪点。

---

## 2. 顶级布局组件范式 (Advanced Layout Components)

### 2.1 双层嵌套倒角外壳 (Double-Bezel Architecture)
杜绝单层卡片的生硬悬浮，模拟精密工业机加工质感：
```tsx
// Outer Shell: 阳极氧化铝托盘质感
<div className="p-1.5 rounded-[2rem] bg-black/5 dark:bg-white/5 ring-1 ring-black/5 dark:ring-white/10">
  // Inner Core: 内嵌精密玻璃核心
  <div className="p-8 rounded-[calc(2rem-0.375rem)] bg-white dark:bg-zinc-900 shadow-[inset_0_1px_1px_rgba(255,255,255,0.15)]">
    {children}
  </div>
</div>
```

### 2.2 按钮内嵌微交互 (Button-in-Button CTA)
```tsx
<button className="group relative inline-flex items-center gap-3 pl-6 pr-2 py-2 rounded-full bg-zinc-900 text-white dark:bg-white dark:text-zinc-950 font-medium active:scale-[0.98] transition-all duration-300">
  <span>探索解决方案</span>
  <span className="w-8 h-8 rounded-full bg-white/10 dark:bg-black/10 flex items-center justify-center group-hover:translate-x-1 group-hover:-translate-y-0.5 transition-transform">
    ↗
  </span>
</button>
```

### 2.3 标题行内微图 (Inline Typography Media)
在主标题文字之间内嵌圆角微图，制造强烈的视觉标点：
```tsx
<h1 className="text-4xl md:text-6xl font-bold tracking-tight text-zinc-900 dark:text-white max-w-5xl">
  构建下一代
  <span className="inline-block w-20 h-9 mx-2 rounded-full bg-cover bg-center align-middle ring-2 ring-black/10" style={{ backgroundImage: "url('/assets/hero-inline.jpg')" }} />
  智能交互系统
</h1>
```

---

## 3. 真实设计系统选型与 Token 契约

| 业务场景 | 推荐官方设计系统 / 依赖库 | 核心价值 |
| :--- | :--- | :--- |
| **现代 SaaS / AI 独立产品** | Tailwind v4 + `motion/react` + Radix UI Primitives | 自由度最高、包体积精简、动效与样式完全自主受控 |
| **可自持组件库体系** | shadcn/ui (`npx shadcn@latest init`) | 拥有源码、易于定制（严格杜绝默认圆角与默认调色盘） |
| **微软生态 / 企业级管理台** | `@fluentui/react-components` | 微软官方体系、原生无障碍、企业级完备性 |
| **IBM 风格 / 深度数据分析** | `@carbon/react` + `@carbon/styles` | 极高数据密度组织模式、严谨设计语言 |
| **开发者工具 / 技术社区** | `@primer/react-brand` (营销) / `@primer/css` | GitHub 官方调性，深受开发者信赖 |
| **公共事业 / 极高无障碍要求** | `govuk-frontend` 或 `uswds` | 法律级无障碍合规与可信度基准 |

### 官方设计系统安装指令备忘
```bash
# Radix Themes
npm install @radix-ui/themes

# shadcn/ui 组件初始化
npx shadcn@latest init
npx shadcn@latest add button card badge separator input dialog

# Fluent UI
npm install @fluentui/react-components

# Carbon Design
npm install @carbon/react @carbon/styles
```
