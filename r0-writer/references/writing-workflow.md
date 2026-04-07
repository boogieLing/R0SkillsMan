# r0-writer Writing Workflow

## 1. Primary Project Context

The live article system sits at:

- `/Volumes/R0sORICO/writing`

When the task happens inside that project, follow its real file layout and scripts first.

Key live files:

- `README.md`
- `templates/article/draft.md`
- `templates/article/outline.md`
- `templates/article/notes.md`
- `templates/article/style.md`
- `templates/article/metadata.yaml`
- `templates/style-presets/*.md`
- `docs/流程图双生成SOP.md`
- `docs/文章配图生成SOP.md`

## 2. Standard Article Package

Default article directory shape:

```text
articles/YYYY-MM-DD-title/
├─ draft.md
├─ outline.md
├─ notes.md
├─ style.md
├─ metadata.yaml
└─ assets/
```

If a new article needs to be created in the live project, prefer:

```bash
./scripts/new-article.sh "文章标题"
```

## 3. File Responsibilities

- `notes.md`
  - raw materials
  - source links
  - facts to verify
  - article idea fragments
  - diagram status notes
- `outline.md`
  - structure lock
  - one core point per section
- `style.md`
  - target reader
  - tone and persona
  - format rules
  - banned words and sentence patterns
- `draft.md`
  - main article body
- `metadata.yaml`
  - status, title, tags, dates, summary

## 4. Preset Selection

Choose the closest preset first, then adapt it:

- `technical-tutorial`
  - for reproducible operations and step-by-step guidance
- `computer-research`
  - for method, evidence, experiments, and boundaries
- `industry-analysis`
  - for market structure, trend judgment, and risk
- `product-presentation`
  - for scenario, value proposition, and CTA

Each article still needs its own `style.md`.

## 5. Core SOP

### SOP-0: Decide the toolbox before writing

- identify the article type
- choose the 1 to 2 core skills or tools
- record the choice in `notes.md` when it matters

### SOP-1: Lock structure before drafting

- finish `outline.md` first
- confirm format rules in `style.md`
- then write `draft.md`

### SOP-2: Keep style per article

- never reuse one `style.md` across multiple articles without adaptation
- if the article direction changes, update `style.md` first

### SOP-3: Polish in order

- lead with the problem and payoff
- delete redundant modifiers and filler
- strengthen key claims with evidence, examples, or steps
- split long paragraphs
- end with a clear next action or conclusion

### SOP-4: Strengthen technical and research articles

- highlight key terms with `<strong>关键词</strong>` when useful
- include at least one diagram when the mechanism is hard to explain with text alone
- provide minimum runnable examples for commands, scripts, configs, or debugging steps

### SOP-5: Global bans

- ban the `不是......而是......` pattern
- ban exposing creative process in the article body
- ban exposing local absolute paths in the article body
- ban Markdown bold `**xx**`

## 6. Diagram Rules

For technical or research-heavy pieces:

- keep both `.mmd` and `.svg`
- keep identical naming and directory
- publish only `.svg`
- record diagram status in `notes.md`

When in the live writing project, consult:

- `docs/流程图双生成SOP.md`

## 7. Illustration Rules

Use article visuals only when they clarify structure, pacing, or recall.

Default visual direction:

- white or very light background
- sharp corners
- technical editorial feel
- structured composition
- semantic colors, not decorative rainbow noise
- no unnecessary text inside generated images

When in the live writing project, consult:

- `docs/文章配图生成SOP.md`

## 8. Final Gate

Before considering the article ready, check:

- first paragraphs state the problem and payoff
- each section carries one core point
- major claims have evidence or explicit caveats
- paragraphs are short enough to scan
- banned sentence patterns are removed
- tone matches the article's `style.md`
- diagrams and assets follow project rules when present
