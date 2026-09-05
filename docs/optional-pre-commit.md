# Optional pre-commit consistency gate / 可选提交前检查

The shipped hook runs this command against the actual Git index:

```powershell
python scripts/workflow.py validate-staged --root .
```

`validate-staged` reads the complete staged snapshot with Git's NUL-delimited index entries and blob objects. It checks required files, JSON, relative Markdown links, public-data patterns, shared Skill consistency, and the generated demo against the **staged** templates. It checks staged deletions and supports spaces and Chinese paths. Unstaged fixes cannot hide an invalid staged file; unfinished unstaged edits do not invalidate a good staged snapshot.

Staged scripts, hooks and tests are treated as data and never executed. The validator itself runs from the working tree. Staged symlinks, submodules, unresolved conflicts and unsafe paths are rejected. Temporary snapshots are confined to `_test-logs/` and cleaned up by the command. If the index changes during checking, the check fails and must be rerun.

The hook is optional and can be bypassed. It is not a security sandbox or a substitute for CI. Git history is intentionally excluded from this frequent check; `validate-repo` checks the working tree and locally available history. In a Git checkout, it skips ignored local files, but includes tracked files even when they match ignore rules. Sensitive-pattern checks are limited heuristics, not a guarantee that all private data is detected.

## Enable only after approval / 批准后启用

Changing `core.hooksPath` is a Git configuration change. The repository never enables the hook automatically. After explicit approval:

```powershell
git config core.hooksPath .githooks
```

Before changing it, record the old value and whether it was unset, so it can be restored. The hook uses an existing `python3`, `python`, or Windows `py -3`; it installs nothing. Missing Python or failed validation blocks the commit.

## CI coverage / CI 检查

[The validation workflow](../.github/workflows/validate.yml) runs on pull requests to `main`, pushes to `main`, and manual dispatch. Windows and Linux jobs run Python tests, the Node audit test, demo/repository/index checks, and an isolated CLI quickstart. Actions are pinned to commit IDs, permissions are read-only, checkout does not persist credentials, and no publish or deployment step exists. CI executes repository code, so its permission boundary matters even though the local staged check only reads code as data.

Adding this file alone does not prove a GitHub run passed or make the checks mandatory. Verify the actual run after publication. Branch protection is a separate repository setting and requires separate approval.

## 中文

Hook 检查的是**准备提交的暂存区内容**。它读取完整暂存快照，使用其中的模板核对生成演示；工作区未暂存的修复不能掩盖坏提交，未完成的工作区草稿也不会误伤好提交。中文、空格、删除和部分暂存都按 Git 索引处理。暂存代码只作为数据读取，符号链接、子模块和未解决冲突会明确拒绝。

完整工作区及本地历史检查保留在 `validate-repo`，CI 同时执行它与测试。Hook 可被绕过，不是沙箱；CI 需要发布后以真实运行结果验收。仓库没有自动启用 Hook、分支保护、安装或发布行为。
