# r0-request 示例库

## 使用说明
- 只复用示例的压缩方式、字段映射方式、最小化假设方式。
- 不要照抄示例中的业务内容。
- 当用户信息不足时，优先参考“示例 4”。

## 示例 1：Web 产品 MVP

### 输入需求
```text
做一个给独立开发者用的 bug 反馈平台。
第一版只要邮箱登录、提交反馈、后台看列表、给反馈打状态。
不要做支付、团队协作、分析报表。
希望先快速上线验证。
```

### 输出要点
- `PROJECT_GOAL` 写成单一目标：验证 bug 反馈闭环，而不是“打造完整 SaaS 平台”。
- `IN_SCOPE_LIST` 只保留登录、反馈提交、状态管理、管理后台。
- `OUT_OF_SCOPE_LIST` 明确写支付、团队权限、统计报表。
- `CURRENT_PHASE` 设为 `Phase 1 - MVP Bootstrap`。
- `TASK_DAG` 采用最短主链：

```text
Task 1 Auth skeleton -> Task 2 Feedback write path -> Task 3 Admin list/status -> Task 4 Minimal validation
```

- `ASSUMPTION:` 可用于说明：暂以邮箱验证码或 magic link 作为最小登录方式。

## 示例 2：多代理代码交付编排

### 输入需求
```text
把一个客服知识库问答系统拆成可并行推进的 agent 任务。
要有 ingestion、检索、回答、评估四段。
先做可跑通版本，不要先搞复杂重排和权限体系。
```

### 输出要点
- `PIPELINE_A` 到 `PIPELINE_N` 可以对应 ingestion、retrieval、answering、evaluation。
- `Custom Agents` 应补最少必要角色，例如 `Agent 7 - Ingestion`、`Agent 8 - Evaluation`。
- `PHASE_1_GOAL` 应写“单轮问答链路可跑通并可验证”。
- `HARD_CONSTRAINTS` 应写无阻塞主路径、索引构建与在线检索解耦。
- `DO_NOT_LIST` 明确禁止提前做 rerank、复杂权限、人工工作流后台。

## 示例 3：纯后端异步服务

### 输入需求
```text
做一个异步转码服务，上传音频后异步转码并回调结果。
要求主路径不阻塞，先支持 mp3 和 wav。
```

### 输出要点
- `NFRS` 应直接落到 `async only`、`no blocking IO in main path`。
- `PIPELINE_A` 可以写 `Upload -> Queue -> Transcode Worker -> Callback`。
- `Agent 6 - Frontend` 可最小化为 `Not used in current phase`。
- `Validation` 应强调输入格式校验、状态机正确性、失败重试。
- `FALLBACK_STRATEGY` 可写：先本地 mock 回调，再接真实回调地址。

## 示例 4：信息不足时的最小可执行输出

### 输入需求
```text
帮我把一个 AI 语音产品想法整理成执行提示词模板。
```

### 输出要点
- 不要臆造产品细节。
- `PROJECT_NAME` 可写 `TBD - AI 语音产品`。
- `SUCCESS_CRITERIA` 可写用户可用动作级描述，而不是编造业务 KPI。
- `LATENCY_TARGET`、`PIPELINE_B`、`KNOWN_ISSUES` 这类无法推出的信息，必须写：

```text
ASSUMPTION: latency target not provided yet; keep as TBD until product constraints are defined.
```

- `TASK_DAG` 保持最短：

```text
Task 1 Clarify core user flow -> Task 2 Define minimal pipeline -> Task 3 Establish validation contract
```

- 最终结果应“结构完整但业务内容克制”，宁可 `TBD`，不要补会误导执行的伪细节。
