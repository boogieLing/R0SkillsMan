# Flat UI Colors US Palette

Source: https://flatuicolors.com/palette/us

Use this palette for the default light HTML shell and architecture diagram accents.

## Core Tokens

| Token | Hex | Recommended Use |
| --- | --- | --- |
| Light Greenish Blue | `#55efc4` | Soft success backgrounds, secondary highlights |
| Mint Leaf | `#00b894` | Backend, storage read path, positive state |
| Faded Poster | `#81ecec` | Light cyan surfaces |
| Green Darner Tail | `#00cec9` | Frontend, primary accent, active indicator |
| Shy Moment | `#a29bfe` | Soft violet backgrounds |
| Exodux Fruit | `#6c5ce7` | Agent, LLM, orchestration, feedback loops |
| City Lights | `#dfe6e9` | Page separators, borders, light grid |
| Soothing Breeze | `#b2bec3` | Muted borders and secondary marks |
| Sour Lemon | `#ffeaa7` | Warning backgrounds |
| Bright Yarrow | `#fdcb6e` | Cloud, queue, async/event paths |
| First Date | `#fab1a0` | Soft risk backgrounds |
| Orangeville | `#e17055` | External service, gateway, control path |
| Pink Glamour | `#ff7675` | Soft security/risk accents |
| Chi-Gong | `#d63031` | Security, failure, blocked path |
| Pico-8 Pink | `#fd79a8` | Product or UI highlight |
| Prunus Avium | `#e84393` | Human review, annotation, policy |
| American River | `#636e72` | Secondary text |
| Dracula Orchid | `#2d3436` | Primary text |

## Default HTML Shell Mapping

- Page background: near-white `#f7fafc` with cards in `#ffffff`.
- Primary text: `Dracula Orchid #2d3436`.
- Secondary text: `American River #636e72`.
- Borders and separators: `City Lights #dfe6e9`.
- Muted dot/list markers: `Soothing Breeze #b2bec3`.
- Primary active accent: `Green Darner Tail #00cec9`.
- Card dots: use `Green Darner Tail`, `Mint Leaf`, `Exodux Fruit`, `Bright Yarrow`, `Chi-Gong`.

## Technical Semantic Mapping

- Frontend / client: `Green Darner Tail #00cec9`.
- Backend / service: `Mint Leaf #00b894`.
- Database / persistent storage: `Exodux Fruit #6c5ce7`.
- Cloud / queue / async: `Bright Yarrow #fdcb6e`.
- Security / auth / risk: `Chi-Gong #d63031`.
- External / edge / gateway: `Orangeville #e17055`.
- Neutral container / boundary: `City Lights #dfe6e9` and `American River #636e72`.

Prefer light tints of these colors for fills and the exact colors for strokes, icons, arrows, and card dots.
