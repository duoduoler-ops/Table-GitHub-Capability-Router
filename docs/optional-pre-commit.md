# Optional pre-commit consistency gate

The deterministic CLI is the primary enforcement mechanism. This repository also ships an optional local Git pre-commit hook that runs:

```powershell
python scripts/workflow.py validate-repo
```

The hook is not enabled automatically because changing `core.hooksPath` is a Git configuration change. After the user explicitly approves that local configuration change, enable it from the repository root:

```powershell
git config core.hooksPath .githooks
```

The hook uses an existing `python3`, `python`, or Windows `py -3` interpreter. It never installs Python or packages. It blocks the commit when repository validation fails or when no existing Python 3 interpreter can run the validator.

The check covers required public files, JSON validity, relative Markdown links, the generated demo, sensitive patterns in the current tree and Git history, and semantic routing consistency through the demo validator.

## 中文

确定性 CLI 是主要校验入口。仓库同时提供一个可选的本地 pre-commit Hook，在提交前运行 `validate-repo`。

Hook 不会自动启用，因为修改 `core.hooksPath` 属于 Git 配置变更。只有使用者明确批准后，才运行：

```powershell
git config core.hooksPath .githooks
```

Hook 只使用本机已有的 `python3`、`python` 或 Windows `py -3`，不安装 Python 或第三方包。仓库文件、JSON、相对链接、生成演示、敏感信息或语义路由一致性校验失败时，提交会被拦截。
