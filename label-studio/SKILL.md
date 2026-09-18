---
name: label-studio
description: 通过 API 检查并安全操作 Label Studio 项目、任务、预测、草稿和标注。用于项目状态、批量标注规划或经审慎授权的批量保存；不用于编写标注配置。
---

# Label Studio 项目操作

此技能用于 Label Studio 项目数据和标注状态工作。标注界面/XML 请求应使用 `create-xml-labeling-config-skill`。

## 安全边界

- 先进行只读检查并给出试运行计划。不得将可见预测或草稿推定为已审核通过的标注。
- 已有标注是持久化保存状态。任务有多个可能结果来源、未验证草稿或审核人/操作历史不清晰时，属于**歧义**，不是可覆盖对象。
- 不得删除任务、标注、预测或项目，不得修改标注配置。
- 任何批量写入前，必须取得明确项目 ID，并在展示试运行结果后获得用户清晰授权。首次写入前必须完成预检；任何歧义来源、缺少核心目标，或点组对象数量异常都会阻断整个批次。备份可能更新的标注，单任务失败后继续执行，并报告任务 ID。

## 认证与发现

从执行环境读取 `LABEL_STUDIO_URL` 和 `LABEL_STUDIO_API_KEY`；未设置时，随附客户端也会加载技能本地 `.env`。旧令牌以 `Authorization: Token <token>` 认证；不得打印令牌。`.env` 保持本地且由 Git 忽略。凭据缺失或被拒绝时，报告该事实，并在检查受保护数据前停止。

实现新的写入路径前，使用官方 Label Studio OpenAPI 规范和本地 API 示例确认已安装版本的行为。`scripts/verify_submit_update_api.py` 会创建和删除自己的、标题明确的临时项目，以验证 POST 创建与 PATCH 更新语义；绝不得指向用户项目。本地 1.23.0 实例中，未保存的前端编辑不出现在 `annotations`、`predictions` 或 `drafts` 中：它是浏览器端状态，不能通过 API 批量保存。

## 标准工作流

1. 运行 `scripts/inspect_project.py --project-id ID` 收集项目和任务状态清单。
2. 运行 `scripts/validate_project.py --project-id ID --fail-on-issues` 校验每个任务声明的 `core_target_labels`，并检查每个相机/点组的已标注区域数是否符合众数。
3. 运行 `scripts/plan_batch_save.py --project-id ID --dry-run` 生成逐任务的保守计划。发现歧义来源或完整性问题时，它返回非零并阻断后续批量操作。
4. 仅在该项目/版本已证实候选结果来源时，解释 `Submit`（创建标注）和 `Update`（修补现有标注）。对本地 1.23.0 部署，不得承诺可通过 API 批量保存未提交的前端编辑。
5. 已授权的写入实现必须先备份，并使单任务失败不致中断整个流程；之后重新检查。

随附脚本均为只读。增加检查字段或显式授权的写入工作流时，参阅 [API 说明](references/api-notes.md)。

## 输出

每项任务保留 `task_id`、标注/预测/草稿数量、选定来源、计划操作和原因。汇总必须区分 `Submit`、`Update`、`Skip`、`Ambiguous` 和 `Failed`；零是有效数量。
