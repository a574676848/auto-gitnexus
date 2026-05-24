---
name: bug-regression-tester
description: 基于 bug 描述、日志、截图、复现步骤或修复 diff 设计并执行回归测试，确保问题可复现、修复后通过，并判断是否沉淀为长期回归用例。适用于“BUG回归测试、修复后验证、为 bug 补测试、复现并防回归”等请求。必须复用 test-governance-core 的 bug 增量规则。
---

# Bug Regression Tester

用于把 bug 修复变成可复用验证资产。

## 流程

1. 使用 `test-governance-core` 收集上下文。
2. 先确认真实环境、真实账号、真实服务、真实测试数据和数据边界；缺少任一必要信息时，**暂停 bug 回归测试执行和正式回归用例沉淀，主动向用户追问缺失项，等用户补齐后立即继续执行**，不得只输出清单后退出。
3. 读取 `references/bug-delta-rules.md`。
4. 提取 bug：症状、入口、复现步骤、实际结果、预期结果、相关日志。
5. 定位影响面和已有测试。
6. 优先写或选择最小失败用例。
7. 修复后重跑同一用例。
8. 判断是否加入长期回归集、冒烟集或仅保留 bug 记录。
9. 默认增量更新 `test-governance/test-cases.md` 中对应 bug 回归用例，并在 `test-governance/reports/` 追加报告。

## 输出

- bug 复现证据。
- 回归测试用例。
- 修复后验证命令和结果。
- 未覆盖风险。
- 是否升级为长期回归。
