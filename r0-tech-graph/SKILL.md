---
name: r0-tech-graph
description: 专门生成浅色优先的技术架构图 HTML 的 skill。用于用户要求“画架构图/系统架构图/技术架构图/流程架构图/数据流架构图/Agent 架构图/网络拓扑图/组件关系图/部署图/可视化系统设计/生成架构图 HTML”时；也适用于英文请求如 generate architecture diagram, draw technical diagram, visualize system architecture, data flow, agent architecture, deployment architecture, network topology. 默认最终产物是对齐 architecture-diagram-generator 的自包含 HTML，但默认改用 Flat UI Colors US 浅色体系，并融合 fireworks-tech-graph 的 SVG 生成、布局、风格、模板、校验和可选 PNG 导出能力。
---

# r0-tech-graph

## Shared Contract

- 执行前优先加载 `../shared/r0-core-contract.md`（若当前仓库存在）。
- 本技能专注“技术架构图”，不要扩展成通用海报、营销页、插画或非技术视觉设计。
- 默认最终产物为浅色自包含 `.html`；HTML 内嵌经过校验的 SVG 架构图。
- `SVG` 是中间产物和可选附带产物；`PNG` 仅在用户要求图片导出、文章配图或验收需要时生成。
- 若在当前项目内产出长期记录，目录使用 `./r0/tech-graph/`；普通图像文件按用户指定路径输出。

## Core Workflow

1. **Classify**：把用户需求归入架构图优先类型。
2. **Extract**：抽取层级、组件、边界、数据流、控制流、依赖、外部系统和风险点。
3. **Plan layout**：先规划画布、分层、分组、箭头路径和图例，再生成文件。
4. **Load references**：默认加载 `references/style-1-flat-icon.md` 和 `references/flat-ui-us-palette.md`；用户指定风格时加载对应 `references/style-N-*.md`。复杂图额外加载 `references/svg-layout-best-practices.md`。
5. **Generate SVG**：优先用 `scripts/generate-from-template.py` 或 Python list method 生成完整 SVG 作为 HTML 主图。
6. **Validate SVG**：运行 `scripts/validate-svg.sh <svg-file>`；若本机有 `rsvg-convert`，再做渲染校验。
7. **Wrap HTML**：用 `scripts/wrap-svg-html.py` 或 `assets/architecture-html-template.html` 生成最终自包含 HTML。
8. **Optional export**：用户要求 PNG 时再运行 `rsvg-convert -w 1920 <svg-file> -o <png-file>`。
9. **Report**：最终回复以 HTML 路径为主，列出附带 SVG/PNG 路径、验证命令与结果。

## Architecture-First Types

优先把请求解释为下面的技术架构图类型：

- **System Architecture**：客户端、网关、服务、存储、中间件、外部依赖、部署边界。
- **Data Flow Architecture**：强调数据从采集、转换、检索、计算到输出的流向。
- **Agent Architecture**：Input、Agent Core、LLM/Planner、Tools、Memory、Output、side effects。
- **Memory Architecture**：Working/Short-term/Long-term/Vector/Graph/External store，区分 read/write path。
- **Deployment / Cloud Architecture**：Region、VPC、Subnet、Cluster、Service、DB、Queue、Security Group。
- **Network Topology**：Internet、Edge、DMZ、Core、Internal、Endpoints、VPN、Firewall。
- **Sequence / Interaction View**：仅当用户要求时序调用、协议交互或跨服务消息顺序时使用。
- **Flowchart / State / ER / UML**：只有当它服务于架构解释时使用，避免偏离技术架构主线。

## Layout Rules

- 架构图默认按层组织：Client -> Edge/Gateway -> Services -> Data/Storage -> External。
- 同层节点水平排列；跨层箭头从上到下或从左到右，保持一个主阅读方向。
- 分组容器用于表达部署边界、团队边界、安全边界或业务域；容器内不要塞满，至少保留 32px 内边距。
- 箭头连接组件边缘，不连接几何中心；优先正交折线，绕过节点和容器标题。
- 2 种以上箭头语义必须加图例；图例放在主图外或最低边界下方，不要压住组件。
- 文本必须可读：组件标题 13-14px，副标题 11-12px，图标题 18-30px；中文文本按实际宽度预留更大空间。
- 所有箭头标签必须有背景底色和 padding，避免被线条穿过。

## Arrow Semantics

使用语义驱动颜色，不要随意换色：

| Flow | Meaning | Suggested style |
| --- | --- | --- |
| `control` | 请求、调用、触发 | solid primary |
| `data` | 数据、文件、上下文 | thicker solid |
| `read` | 读取、检索、查询 | green/blue solid |
| `write` | 写入、持久化、索引 | green dashed |
| `async` | MQ、事件、回调 | dashed gray/orange |
| `feedback` | 循环、重试、agent loop | curved purple |

## Styles

- 默认使用浅色 HTML shell + `Style 1 Flat Icon` SVG：白底，适合文档、公众号、PPT。
- 默认色系使用 Flat UI Colors US，详见 `references/flat-ui-us-palette.md`。
- 架构评审、研发文档可用 `Style 2 Dark Terminal` 或 `Style 3 Blueprint`。
- 产品化或对外说明可用 `Style 4 Notion Clean`、`Style 6 Claude Official`、`Style 7 OpenAI Official`。
- 需要详细选型时加载 `references/style-diagram-matrix.md`。

## Default Light Theme

HTML 外壳默认使用浅色，不再沿用 `architecture-diagram-generator` 的深色默认：

- Page background: near-white `#f7fafc`
- Surface/card: white `#ffffff`
- Border/grid: City Lights `#dfe6e9`
- Primary text: Dracula Orchid `#2d3436`
- Secondary text: American River `#636e72`
- Primary accent: Green Darner Tail `#00cec9`
- Backend/storage accent: Mint Leaf `#00b894`
- Agent/LLM/database accent: Exodux Fruit `#6c5ce7`
- Cloud/async accent: Bright Yarrow `#fdcb6e`
- Security/risk accent: Chi-Gong `#d63031`

仅当用户明确要求“深色/暗色/dark terminal/dark themed”时，才使用 `--theme dark` 或深色 SVG style。

## Scripts

### Generate from template

用内置模板生成起稿 SVG，适合节点和箭头已经结构化的场景：

```bash
python3 ./scripts/generate-from-template.py architecture ./output/arch.svg \
  '{"title":"My Architecture","nodes":[],"arrows":[],"legend":[]}'
```

推荐在 arrow JSON 中使用 `source` / `target` 节点 id，让脚本把箭头吸附到节点边缘；`x1,y1,x2,y2` 只作为 fallback。

### Validate SVG

```bash
./scripts/validate-svg.sh ./output/arch.svg
rsvg-convert ./output/arch.svg -o /tmp/r0-tech-graph-test.png
```

### Wrap final HTML

默认最终产物必须生成 HTML：

```bash
python3 ./scripts/wrap-svg-html.py ./output/arch.svg ./output/arch.html \
  --title "My System Architecture" \
  --subtitle "Layered architecture view with data and control flows"
```

浅色是默认主题；深色只在用户明确要求时使用：

```bash
python3 ./scripts/wrap-svg-html.py ./output/arch.svg ./output/arch.html --theme dark
```

可用 `--cards` 传入摘要卡片 JSON：

```bash
python3 ./scripts/wrap-svg-html.py ./output/arch.svg ./output/arch.html \
  --cards '[{"title":"Runtime","color":"cyan","items":["API gateway","Service layer","Async worker"]}]'
```

### Optional PNG export

仅当用户要求 PNG 或需要图片配图时导出：

```bash
rsvg-convert -w 1920 ./output/arch.svg -o ./output/arch.png
```

## HTML Architecture Output

最终输出必须是“浅色优先的自包含 HTML / 可直接打开的架构图页面”。优先路径：

1. 先用 `fireworks-tech-graph` 继承来的脚本、模板和 style references 生成高质量 SVG。
2. 再用 `scripts/wrap-svg-html.py` 把 SVG 嵌入 HTML，并补充标题、摘要卡片和 footer。
3. 如果需要手工深度定制 HTML 页面，再复制并改写：

`assets/architecture-html-template.html`

HTML 形态继承 `architecture-diagram-generator` 的核心模式，但默认改为浅色：

- JetBrains Mono
- Flat UI Colors US light shell
- inline SVG
- semantic colors for frontend/backend/database/cloud/security/message bus
- summary cards below the diagram
- no JavaScript required

HTML 输出仍需检查 SVG 区域的重叠、箭头穿透、图例位置、横向滚动和摘要卡片文本溢出。

## Technical Rules

- SVG 必须包含 `xmlns="http://www.w3.org/2000/svg"` 和明确 `viewBox`。
- 不使用外部字体 `@import`；在 SVG 内用系统字体或 `<style>` 指定字体栈。
- 文本内容必须 XML escape，尤其是 `&`, `<`, `>`。
- 箭头 marker 必须在 `<defs>` 定义，`marker-end="url(#...)"` 引用必须存在。
- 复杂 SVG 使用 Python list method 逐行生成，避免 heredoc 截断或引号错误。
- 最多自动修复两轮；第三次仍失败时停止并报告根因、坏文件路径和下一步。

## Output Contract

最终回复使用中文，包含：

1. `产物路径`：HTML 绝对路径为第一项；随后列出 SVG 中间产物和可选 PNG。
2. `验证结果`：运行过的校验命令和是否通过。
3. `图内容摘要`：架构层级、关键组件、关键流向。
4. `限制 / 风险`：无法从需求中确认的假设、未画出的边界或待用户确认事项。
