# Example OpenViking Report

本文件是当前仓库的验证样例，不是通用规则。其他项目只能借鉴格式，不能照抄技术栈。

## 测试治理报告

- 目标：验证通用测试 skill 能识别 monorepo 测试入口，并执行代表性测试。
- 项目/模块：`E:\zbg\openviking-knowdge`
- 建议落盘：`test-governance/test-cases.md`、`test-governance/reports/`、`test-governance/evidence/`
- 上下文来源：根 `package.json`、`pnpm-workspace.yaml`、`apps/server/package.json`、`apps/web/package.json`、`packages/ova-cli/package.json`、现有测试文件。
- 知识库通道：可选。OVA MCP/CLI 可增强项目知识，但不可阻塞本地测试治理。
- 技术栈识别：Node monorepo、pnpm workspace、server Jest、web Vitest、web Playwright、ova-cli Jest。
- 现有测试入口：
  - `pnpm --filter @openviking-admin/ova-cli run test`
  - `pnpm --filter server run test -- app.controller.spec.ts`
  - `pnpm --filter web run test -- lib/apiClient.spec.ts`
- 测试类型：CLI 回归、后端基础集成/单元、前端逻辑测试。
- 覆盖范围：代表性轻量验证，不代表全量发布门禁。
- 排除范围：未执行 Playwright UI、全量 server/web 测试、真实 OVA 知识库检索。
- 执行命令：
  - `pnpm --filter @openviking-admin/ova-cli run test` -> 31/31 通过。
  - `pnpm --filter server run test -- app.controller.spec.ts` -> 1/1 通过。
  - `pnpm --filter web run test -- lib/apiClient.spec.ts` -> 5/5 通过。
- 风险判断：代表性验证通过；若用于发布，还需执行全量测试、UI 冒烟和文档检查。

## 已发现并修正的规则

- 在 pnpm workspace 子包内运行测试时，文件参数应使用子包内相对路径，如 `lib/apiClient.spec.ts`。
- 使用根相对路径 `apps/web/lib/apiClient.spec.ts` 会导致 Vitest 报 `No test files found`，不能误判为测试缺失。
- 技术栈检测脚本必须排除 `node_modules`、`.git`、`dist`、`build`、`.next` 等大目录，避免递归超时。
