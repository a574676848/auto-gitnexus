# Stack Detection

按文件证据识别，不凭经验猜。

| 证据 | 技术栈 | 常见命令 |
| --- | --- | --- |
| `package.json` | Node / Web / CLI | `npm test`、`pnpm test`、`yarn test` |
| `playwright.config.*` | Web UI | `playwright test` 或 package script |
| `cypress.config.*` | Web UI | `cypress run` 或 package script |
| `vitest.config.*` | Node / Web unit | `vitest run` |
| `jest.config.*` 或 package jest | Node / Nest / React | `jest` |
| `pyproject.toml`、`pytest.ini` | Python | `pytest` |
| `pom.xml` | Java Maven | `mvn test` |
| `build.gradle*` | Java/Kotlin Gradle | `gradle test` |
| `go.mod` | Go | `go test ./...` |
| `Cargo.toml` | Rust | `cargo test` |
| `.sln`、`.csproj` | .NET | `dotnet test` |
| `composer.json` | PHP | `vendor/bin/phpunit` |
| `Gemfile` | Ruby | `bundle exec rspec` |

优先读取项目已有 scripts、CI、Makefile、Justfile、Taskfile。只有缺少明确入口时，才使用常见命令作为候选，并标记为“建议命令”而非“已验证命令”。

命令选择顺序：

1. 项目文档明确给出的命令。
2. CI 中实际运行的命令。
3. package/build 配置中的 scripts。
4. 技术栈默认命令。

Monorepo 注意事项：

- 使用 workspace filter 进入子包执行时，测试文件参数通常应使用子包内相对路径，例如 `lib/apiClient.spec.ts`，不要传仓库根相对路径 `apps/web/lib/apiClient.spec.ts`。
- 如果命令提示 `No test files found`，先检查工作目录和参数路径，不要直接判断测试缺失。
- 根目录执行全量测试时再使用根相对路径或项目自身支持的 filter。
