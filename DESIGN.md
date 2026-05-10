---
name: cowork-render dark
version: "2"
description: Canonical visual identity for every renderer cowork-render produces (kanban, dashboard, timeline, future shapes). GitHub-dark cool-neutral base + Monokai-saturated accents — source of truth for every renderer.

colors:
  # Backgrounds — GitHub/Discord cool-neutral dark
  bg-base: "#0d1117"            # GitHub dark canonical, very dark with subtle blue undertone
  bg-surface: "#161b22"         # card/panel surface, slight lift
  bg-surface-raised: "#21262d"  # raised UI, column headers
  bg-surface-hover: "#30363d"   # hover state
  bg-code: "#010409"            # darker than base for code-span/code-block contrast
  bg-input: "#161b22"

  # Text — cool cream
  text-base: "#e6edf3"          # GitHub's primary text
  text-heading: "#f0f6fc"       # slightly brighter for headings
  text-muted: "#8b949e"         # GitHub's muted gray — passes WCAG AA on bg-base
  text-strong: "#c9d1d9"        # subsection headings, intermediate emphasis
  text-code: "#A6E22E"          # keep Monokai green for inline code — pops vividly against cool base

  # Borders
  border-subtle: "#30363d"      # GitHub's border-default
  border-emphasis: "#484f58"    # slightly stronger for emphasis

  # Severity ramp — Monokai accents preserved
  severity-high: "#F92672"      # Monokai pink/magenta
  severity-medium: "#FD971F"    # Monokai orange
  severity-low: "#E6DB74"       # Monokai yellow
  severity-info: "#8b949e"      # GitHub muted gray (replaces Monokai's #75715E — reads muddy on cool base)
  severity-ok: "#A6E22E"        # Monokai green

  # Links — Monokai cyan + purple
  link: "#66D9EF"               # Monokai cyan
  link-visited: "#AE81FF"       # Monokai purple
  link-hover: "#9EE5F5"

typography:
  body:
    fontFamily: Georgia, 'Times New Roman', serif
    fontSize: 17px
    lineHeight: 1.7
  heading:
    fontFamily: Georgia, 'Times New Roman', serif
    fontWeight: 600
  mono:
    fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', Menlo, Consolas, monospace"
    fontSize: 0.92em
  meta:
    fontFamily: "'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace"
    fontSize: 0.85rem
  card-title:
    fontFamily: Georgia, 'Times New Roman', serif
    fontSize: 1rem
    fontWeight: normal

rounded:
  sm: 4px        # code-spans, small pills
  md: 6px        # buttons, inputs
  lg: 10px       # cards, panels (modern card radius)
  pill: 999px    # status pills, count badges

spacing:
  xs: 0.25rem
  sm: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  xxl: 2rem
---

# cowork-render — Visual Identity

## Overview

GitHub-dark cool-neutral background with Monokai-saturated accents — the most-recognized modern doc-site palette paired with the most-recognized dev-tool accent system. The base and neutral surfaces use GitHub's cool-dark grays (`#0d1117` → `#161b22` → `#21262d`), while severity signals, links, and code accents stay fully Monokai-saturated: vivid pink, orange, yellow, green, cyan, and purple against the cool base pop harder than they did against the warm-olive Monokai background — the contrast is sharper, the hierarchy reads cleaner.

Every cowork-render output should feel like part of one family — same palette, same font choices, same spacing rhythm — whether the shape is a kanban, a dashboard, or a timeline.

## Colors

**Backgrounds** cool from `bg-base` (`#0d1117`, GitHub's canonical dark) through `bg-surface` (`#161b22`) through `bg-surface-raised` (`#21262d`) through `bg-surface-hover` (`#30363d`). Cool-neutral with a subtle blue undertone — the most-recognized dark-mode palette in modern developer tooling. `bg-code` (`#010409`) sits slightly darker than `bg-base` for code-span and code-block contrast.

**Text** anchors on GitHub's cool cream: `text-base` (`#e6edf3`) for primary prose, `text-heading` (`#f0f6fc`) for headings, `text-muted` (`#8b949e`) for secondary/muted content. `text-muted` passes WCAG AA at ~7:1 on `bg-base`. `text-code` uses Monokai green (`#A6E22E`) for inline code accents — pops vividly against the cool base.

**Severity** maps to Monokai's vivid accent colors: pink/magenta for high (`#F92672`), orange for medium (`#FD971F`), yellow for low (`#E6DB74`), green for ok (`#A6E22E`). `severity-info` uses GitHub's muted gray (`#8b949e`) rather than Monokai's `#75715E` — Monokai's comment color was tuned for code editors (intentionally dim) and reads muddy against the cool base; `#8b949e` is the right readable-but-subdued gray for prose info-tier content.

**Links** use Monokai cyan (`#66D9EF`) as the primary link color. Cyan is distinctive from both heading and body text, and against the cool-dark base it pops cleanly without fighting the severity accents. Visited links shift to Monokai purple (`#AE81FF`). Hover lightens to `#9EE5F5`.

## Typography

Body in Georgia serif — readable for long-form prose, conveys document-rather-than-app feel. Body font size is 17px (bumped from 15px for comfortable reading in browser contexts), line-height 1.7.

**JetBrains Mono** leads the monospace stack, with Fira Code → SF Mono → Menlo → Consolas → generic monospace as fallbacks. JBM has strong readability characteristics at small sizes, excellent ligature support, and is common on developer workstations. The font must be installed system-wide to render — no WOFF2 bundle, no CDN fetch. The fallback chain degrades gracefully on machines without JBM; the system mono stack covers every environment. Mono size is 0.92em; meta/timestamp contexts use 0.85rem.

## Layout primitives

`rounded.sm` (4px) for inline code spans and small pills. `rounded.md` (6px) for buttons and inputs. `rounded.lg` (10px) for cards and panels (modern card radius, matches GitHub/Linear/Vercel). `rounded.pill` (999px) for status pills and count badges (full ellipse).

Spacing scale runs from `xs` (4px) through `xxl` (32px) on a roughly 1.5x ratio. Use `xs/sm` for tight inline contexts (badge padding, code-span padding), `md/lg` for card content, `xl/xxl` for section spacing.

## Do's and don'ts

**Do** consume colors and dimensions via CSS variables (`var(--bg-base)`, `var(--severity-high)`, etc.) — never hardcode hex values in renderer modules.

**Do** add new tokens here when a real renderer need arises that the existing palette doesn't cover. Update the CSS variables block automatically via the loader.

**Don't** import a renderer-specific palette inline. The whole point is consolidation.

**Don't** use the severity colors for non-severity purposes (e.g., decorative accents). They carry semantic weight; misuse dilutes the signal.

**Don't** add a light-mode variant. Single dark theme is canonical.
