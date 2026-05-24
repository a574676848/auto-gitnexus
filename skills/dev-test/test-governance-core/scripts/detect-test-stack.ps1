param(
    [string]$Path = "."
)

$root = Resolve-Path -LiteralPath $Path
$signals = @()
$excludedDirs = @('.git', 'node_modules', 'dist', 'build', '.next', 'coverage', 'target', 'bin', 'obj')

function Add-Signal([string]$Kind, [string]$File, [string]$Command) {
    $script:signals += [pscustomobject]@{
        kind = $Kind
        file = $File
        command = $Command
    }
}

if (Test-Path -LiteralPath (Join-Path $root "package.json")) {
    Add-Signal "node" "package.json" "npm test / pnpm test / yarn test"
}
if (Test-Path -LiteralPath (Join-Path $root "pnpm-workspace.yaml")) {
    Add-Signal "node-monorepo" "pnpm-workspace.yaml" "pnpm -r --if-present run test"
}

function Find-Config([string[]]$Names) {
    $queue = [System.Collections.Generic.Queue[System.IO.DirectoryInfo]]::new()
    $queue.Enqueue((Get-Item -LiteralPath $root))

    while ($queue.Count -gt 0) {
        $dir = $queue.Dequeue()
        foreach ($name in $Names) {
            if (Get-ChildItem -LiteralPath $dir.FullName -File -Filter $name -ErrorAction SilentlyContinue) {
                return $true
            }
        }

        foreach ($child in Get-ChildItem -LiteralPath $dir.FullName -Directory -ErrorAction SilentlyContinue) {
            if ($excludedDirs -notcontains $child.Name) {
                $queue.Enqueue($child)
            }
        }
    }

    return $false
}

if (Find-Config @("playwright.config.*")) {
    Add-Signal "web-ui-playwright" "playwright.config.*" "playwright test"
}
if (Find-Config @("cypress.config.*")) {
    Add-Signal "web-ui-cypress" "cypress.config.*" "cypress run"
}
if (Find-Config @("vitest.config.*")) {
    Add-Signal "node-vitest" "vitest.config.*" "vitest run"
}
if (Find-Config @("jest.config.*")) {
    Add-Signal "node-jest" "jest.config.*" "jest"
}
if (Test-Path -LiteralPath (Join-Path $root "pyproject.toml")) {
    Add-Signal "python" "pyproject.toml" "pytest"
}
if (Test-Path -LiteralPath (Join-Path $root "pom.xml")) {
    Add-Signal "java-maven" "pom.xml" "mvn test"
}
if (Get-ChildItem -LiteralPath $root -File -Include "build.gradle","build.gradle.kts" -ErrorAction SilentlyContinue) {
    Add-Signal "java-gradle" "build.gradle*" "gradle test"
}
if (Test-Path -LiteralPath (Join-Path $root "go.mod")) {
    Add-Signal "go" "go.mod" "go test ./..."
}
if (Test-Path -LiteralPath (Join-Path $root "Cargo.toml")) {
    Add-Signal "rust" "Cargo.toml" "cargo test"
}
if (Get-ChildItem -LiteralPath $root -File -Include "*.sln","*.csproj" -ErrorAction SilentlyContinue) {
    Add-Signal "dotnet" "*.sln/*.csproj" "dotnet test"
}

$signals | ConvertTo-Json -Depth 4
