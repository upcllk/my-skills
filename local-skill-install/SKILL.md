---
name: local-skill-install
description: 在 custom-skills 工作区维护本地 agent skill 源目录，并通过符号链接安装到 ~/.agents/skills。适用于创建、更新、链接安装或安全移除本地技能。
---

# 安装本地技能

每个技能源目录必须是 `custom-skills` 工作区的直接子目录，并通过符号链接安装到 `~/.agents/skills`；不得直接在 `~/.agents/skills` 创建或复制技能。

每个通过此流程安装的技能都以 `~/.agents/skills/<skill-name>` 作为 Codex 和 GitHub Copilot 共用的发现入口，并指向 `<custom-skills-workspace>/<skill-name>`。无论由哪个客户端调用，始终维护同一份源文件。

## 创建源技能

将技能创建为 `custom-skills` 工作区的直接子目录。可用 `skill-creator` 时遵循其说明，并根据实际位置解析所提供的初始化脚本；不得假定某个客户端专属的内部路径。否则手动创建源技能。

在创建链接前完成编写和校验。文件夹名称即为技能名称。

## 校验源技能

- 使用已确认位置的可用技能校验器，例如 `quick_validate.py`，并遵循源技能提出的额外校验要求。
- 没有校验器时，进行明确的基础检查：源目录是工作区直接子目录；`SKILL.md` 有有效 YAML frontmatter 且 `name`、`description` 非空；名称与文件夹相同，并且仅使用小写字母、数字和连字符；所有引用的本地文件存在。
- 报告基础检查时须明确称为“基础检查”，不得称为校验器成功运行。必需检查无法完成或校验器失败时，报告并解决问题后才能链接；不得以基础检查绕过失败的校验器。
- 不得仅为获取创建器或校验器而自动安装工具。

## 以符号链接安装

- 使用符号链接，源文件修改后无需重新安装即可生效。
- 替换已有安装链接属于破坏性操作。先检查目标；只有获得明确批准后才可传入 `--replace`。

## 安装步骤

1. 创建或替换链接前完成上述源技能校验。
2. 使用文件夹名作为已安装的技能名；随附安装器会从该文件夹生成链接名。
3. 运行随附安装器。默认创建符号链接，且拒绝覆盖指向其他技能的已有目标。

```bash
python3 /path/to/custom-skills/local-skill-install/scripts/install_local_skill.py \
  /path/to/custom-skills/my-skill
```

当安装器本身通过另一个 checkout 的软链接调用，而源 skill 位于另一个
`custom-skills` 工作区时，显式指定源工作区：

```bash
python3 /path/to/my-skills/local-skill-install/scripts/install_local_skill.py \
  --workspace-root /path/to/custom-skills \
  /path/to/custom-skills/my-skill
```

在命令后添加 `--dry-run` 可预览链接操作。安装器始终链接到 `~/.agents/skills`。

## 更新或移除

- 编辑并校验源技能；正确的既有链接无需重新创建。若消费端未自动读取变更，再重启或重新加载该客户端。
- 不得用复制安装替代链接，始终保留“源目录 + 链接”的布局。
- 移除链接前，先解析并展示精确目标。只有在用户明确批准后，才能移除该命名目录或链接；不得使用宽泛的递归删除命令。

## 核验

安装后确认 `~/.agents/skills/<skill-name>` 是指向预期源目录的符号链接，且能通过该链接访问 `SKILL.md`。

报告源目录、符号链接目标、源技能校验方法与结果，以及是否可能需要重启/重新加载 agent。
