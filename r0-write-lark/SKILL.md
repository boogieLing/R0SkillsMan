---
name: r0-write-lark
description: 使用自然语言把本地文章目录同步到 Lark 云文档。适用于“同步某篇文章到 Lark/飞书”场景；会先按关键词匹配文章目录，再自动调用 Codex MCP 的 docx.builtin.import，并回写 metadata.yaml。
---

# r0-write-lark

## 何时使用
当用户表达以下意图时使用本技能：
- “同步《提示词指导》到 Lark”
- “把 writing 项目实战这篇文章发布到飞书”
- “根据文章名自动找到目录并导入云文档”

## 前置条件
1. 已配置 Lark MCP（推荐服务器名：`lark`）。
2. 已完成 `lark-mcp login`，可使用用户令牌。
3. 本地文章按“一篇文章一个文件夹”组织。

## 可配置项（不要写死）
1. Skill 名称：可用任意前缀，例如 `team-write-lark`、`acme-write-lark`。
2. 文章目录：通过 `--articles-dir`/`--article-root` 或环境变量 `WRITE_LARK_ARTICLES_DIR` 指定。
3. MCP 服务名：通过 `--server-name` 或环境变量 `LARK_MCP_SERVER_NAME` 指定。
4. 入口脚本路径：通过 `WRITE_LARK_SCRIPT` 或 `R0_WRITE_LARK_SCRIPT` 指定。
5. 日志前缀：通过 `WRITE_LARK_LOG_PREFIX` 指定。
6. 流程图模式：`--diagram-mode external-image|keep` 或 `WRITE_LARK_DIAGRAM_MODE`。
7. 外站渲染参数：`--diagram-format png|svg`、`--mermaid-base-url`，或环境变量 `WRITE_LARK_DIAGRAM_FORMAT`、`WRITE_LARK_MERMAID_BASE_URL`。
8. Mermaid 朴素模式：`--mermaid-plain true|false` 或 `WRITE_LARK_MERMAID_PLAIN`（默认 `true`，导入时移除 class/style 颜色定义）。
9. 公式模式：`--latex-mode external-image|keep` 或 `WRITE_LARK_LATEX_MODE`。
10. 公式渲染参数：`--latex-format png|svg`、`--latex-base-url`，或环境变量 `WRITE_LARK_LATEX_FORMAT`、`WRITE_LARK_LATEX_BASE_URL`。
11. 自动重登开关：`--auto-reauth true|false` 或 `WRITE_LARK_AUTO_REAUTH`（默认 `true`）。
12. 自动登录凭证：`--lark-app-id`、`--lark-app-secret`，或 `WRITE_LARK_APP_ID`、`WRITE_LARK_APP_SECRET`。
13. 登录回调参数：`WRITE_LARK_OAUTH_HOST`、`WRITE_LARK_OAUTH_PORT`、`WRITE_LARK_OAUTH_DOMAIN`。
14. 登录 scope：`WRITE_LARK_OAUTH_SCOPE`（默认 `docs:doc drive:drive docs:document.media:upload`）。

## 执行流程
1. 调用脚本：`scripts/sync_article.sh "自然语言指令"`。
2. 脚本自动执行：
- 解析自然语言关键词。
- 在 `articles/` 下匹配最可能的文章目录。
- 选取同步文件（优先成稿 `.md`，其次 `draft.md`）。
- 通过 `codex exec` 调用 MCP 工具 `docx.builtin.import`。
- 若遇到 `Current user_access_token is invalid or expired` / `access_token` 相关错误，会自动拉起 `lark-mcp login`，并自动重试导入一次（默认开启）。
- 导入成功后回写 `metadata.yaml`：`lark_doc_url`、`lark_doc_token`、`lark_sync_at`。
- 默认会把 Markdown 中的 Mermaid 代码块转换为外站透明底流程图链接（默认 `https://mermaid.ink`，`png`）。
- 默认会把 Markdown 中的 LaTeX 公式（`$$...$$`、`\[...\]`、可识别的行内 `$...$`）转换为外站透明底公式图（默认 `https://latex.codecogs.com`，`png`）。
- 默认会把 `<span style="...">术语</span>` 转为 Lark 稳定可见的强调格式：路径/代码术语优先转行内 `code`，其余文本统一回退为 Markdown 粗体 `**...**`。
- 不对原有 Markdown 粗体做二次语义改写，保持原文强调语气与阅读节奏。
- 对本地图片执行门禁：若存在同名 `.mmd`，自动修复为 Mermaid 外链；若无法自动修复则中止同步并输出待处理清单（避免“同步成功但图片丢失”）。
- 对内嵌 SVG 执行门禁：检测到 `<svg>` 将直接中止，提示改为 Mermaid 代码块或 https 图片（避免导入后样式丢失）。
- 以上兼容转换仅用于“同步飞书”时的临时导入文件，不会改写文章源文件。
- 结束时必须输出文档地址：
  - `LARK_DOC_URL=<url>`
  - `LARK_DOC_TOKEN=<token>`
  - `LARK_IMPORT_STATUS=success`

## 结果输出规范
当此 skill 在对话中执行完成后，最终回复必须包含：
1. 第一行：`Lark 文档地址：<url>`
2. 第二行：`Token：<token>`（可选）
3. 第三行：`同步状态：success/failed`

## 快速命令
```bash
# 在任意目录执行（用参数传入 articles）
~/.codex/skills/r0-write-lark/scripts/sync_article.sh \
  --articles-dir "<YOUR_ARTICLES_DIR>" \
  "同步提示词指导的文章"
```

## 常用参数
```bash
# 仅匹配，不执行导入
~/.codex/skills/r0-write-lark/scripts/sync_article.sh \
  --articles-dir "<YOUR_ARTICLES_DIR>" \
  --dry-run "同步提示词指导"

# 指定 articles 目录
~/.codex/skills/r0-write-lark/scripts/sync_article.sh \
  --articles-dir "<YOUR_ARTICLES_DIR>" \
  "同步 writing项目实战"

# 不回写 metadata
~/.codex/skills/r0-write-lark/scripts/sync_article.sh \
  --articles-dir "<YOUR_ARTICLES_DIR>" \
  --no-metadata "同步提示词指导"

# 保留 Mermaid 代码块，不做外站图转换
~/.codex/skills/r0-write-lark/scripts/sync_article.sh \
  --articles-dir "<YOUR_ARTICLES_DIR>" \
  --diagram-mode keep "同步提示词指导"

# 保留 LaTeX 原文，不做公式图转换
~/.codex/skills/r0-write-lark/scripts/sync_article.sh \
  --articles-dir "<YOUR_ARTICLES_DIR>" \
  --latex-mode keep "同步提示词指导"

# 通过环境变量指定目录与日志前缀
export WRITE_LARK_ARTICLES_DIR="<YOUR_ARTICLES_DIR>"
export WRITE_LARK_LOG_PREFIX="team-write-lark"
~/.codex/skills/r0-write-lark/scripts/sync_article.sh "同步提示词指导"
```

## 失败处理
1. 没找到匹配目录：用更具体的文章名重试。
2. MCP 调用失败：先确认 `codex mcp list` 中 `lark` 已启用。
3. `login` 报 `too many arguments`：把多个 scope 放进一个字符串，例如 `--scope "docs:doc,drive:drive,docs:document.media:upload"`。
4. `错误码 20027`：应用未开通 `offline_access`，从 scope 里移除它或先申请后再登录。
5. `Access denied`（缺 scope）：在应用权限管理补齐 `docs:doc`、`drive:drive`、`docs:document.media:upload`，发布版本后重登。
6. `Current user_access_token is invalid or expired`：重新登录后再同步，示例（不含 `offline_access`）：
```bash
npx -y @larksuiteoapi/lark-mcp login \
  -a <APP_ID> \
  -s <APP_SECRET> \
  -d https://open.larksuite.com \
  --host 127.0.0.1 \
  -p 3000 \
  --scope "docs:doc drive:drive docs:document.media:upload"
```
7. 新版脚本默认会在 token 失效时自动拉起登录并重试一次；只有自动重登失败或被关闭（`--auto-reauth false`）时，才需要手动执行上述登录命令后重跑。
