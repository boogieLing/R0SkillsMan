# 提交记录模板

## 1. 基本信息
- 项目路径：
- 工作开始时间：
- 工作结束时间：
- 本次工作目的（一句话）：

## 2. 分点功能清单
1.
2.
3.

## 3. 审查摘要（r0-review）
- 审查结论：
- 阻断项（critical/high）：
- 其余风险（medium/low）：
- 待确认项：

## 4. 提交拆分决策
- 是否拆分多次 commit：
- 拆分依据：

## 4. 影响面分析
- 功能与模块影响：
- 数据与状态影响：
- 外部行为影响：
- 运行时影响：
- 风险与回滚影响：
- 综合风险等级（high/medium/low）：

## 5. 提交拆分决策
- 是否拆分多次 commit：
- 拆分依据：

## 6. 提交清单
1. type:
   message:
   commit id:
2. type:
   message:
   commit id:

## 7. Git 状态核查
- 提交前 `git status --short --branch` 摘要：
- 提交后 `git status --short --branch` 摘要：
- 是否存在超出基线的新业务代码改动：

## 8. 本地记录与忽略规则
- 记录文件路径：
- `.gitignore` 是否包含 `r0-submit/`：
- 是否已确保 `r0-submit/` 不在 staged：
