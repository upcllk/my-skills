---
name: skill-publisher
description: 将选定的本地 skill 迁移到远端多 skill Git 仓库，并在 custom-skills 原位置建立软链接；适用于保留本地 skill 入口、拆分本地与 GitHub 管理边界的场景。
---

# Skill Publisher

用于维护以下布局：

```text
custom-skills/<skill-name> -> ../skill-repos/my-skills/<skill-name>
~/.agents/skills/<skill-name> -> custom-skills/<skill-name>
```

远端仓库可以在一个 checkout 中管理多个 skill；未迁移的 skill 继续由 `custom-skills` 父仓库管理。

## 迁移前

- 只处理用户明确列出的 skill，不根据目录内容自行扩大范围。
- 确认每个 skill 是 `custom-skills` 的直接子目录，并完成 skill 校验；至少确认 `SKILL.md` 存在。
- 确认父仓库和远端 checkout 没有未提交改动，远端目标目录不存在。
- 先运行脚本的 dry-run；只有用户明确要求执行迁移时才使用 `--apply`。
- 迁移不负责创建 GitHub 仓库。远端仓库应先被 clone 到 `skill-repos/<repo-name>`，并确认目标为正确仓库。

## 迁移

在 `custom-skills` 根目录执行：

```bash
python3 skill-publisher/scripts/migrate_to_remote.py \
  --remote-root ../skill-repos/my-skills \
  gif-transparent-background label-studio
```

确认预览内容无误后：

```bash
python3 skill-publisher/scripts/migrate_to_remote.py \
  --remote-root ../skill-repos/my-skills \
  --apply \
  gif-transparent-background label-studio
```

脚本会把实体目录移动到远端 checkout，使用 `git rm --cached` 从父仓库索引移除原文件，在原位置创建绝对软链接，并把这些链接加入 `.git/info/exclude`。它不会覆盖已有目录或软链接，也不会自动 commit 或 push。

迁移后核验：

```bash
test -f custom-skills/<skill-name>/SKILL.md
test -f ~/.agents/skills/<skill-name>/SKILL.md
git -C ../skill-repos/my-skills status
git status
```

## 发布

迁移完成并检查远端 checkout 后，在远端仓库中由用户明确提交和推送：

```bash
git -C ../skill-repos/my-skills add <skill-name>...
git -C ../skill-repos/my-skills commit -m "add or update skills"
git -C ../skill-repos/my-skills push origin main
```

已有软链接不需要重新安装；如果消费端没有自动读取变更，再重启或重新加载 agent。
