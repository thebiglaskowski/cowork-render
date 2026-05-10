---
name: cowork-render dark
version: "2"
description: Canonical visual identity for every renderer cowork-render produces (kanban, dashboard, timeline, future shapes). Monokai-inspired palette — source of truth for every renderer.

colors:
  # Backgrounds — Monokai-warm dark
  bg-base: "#272822"            # classic Monokai background, warm dark
  bg-surface: "#3E3D32"         # card/panel surface, subtle lift
  bg-surface-raised: "#36352B"  # chip/badge/pill bg — darker inset for embedded labels
  bg-surface-hover: "#5A594F"   # hover state
  bg-code: "#1E1F1C"            # deeper for code-span/code-block contrast
  bg-input: "#3E3D32"

  # Text — Monokai cream
  text-base: "#F8F8F2"          # primary body cream
  text-heading: "#FFFFFF"       # headings get pure white pop
  text-muted: "#ABA994"         # brightened from Monokai's #75715E to pass WCAG AA on bg-base
  text-strong: "#F8F8F2"        # subsection headings, secondary headings
  text-code: "#A6E22E"          # Monokai green for inline code

  # Borders
  border-subtle: "#49483E"
  border-emphasis: "#75715E"

  # Severity ramp — Monokai-mapped
  severity-high: "#F92672"      # Monokai pink/magenta — vivid signal for real problems
  severity-medium: "#FD971F"    # Monokai orange — ghost projects, hub inconsistencies
  severity-low: "#E6DB74"       # Monokai yellow — tag drift, stale docs
  severity-info: "#75715E"      # Monokai comment gray — orphans, low-priority info
  severity-ok: "#A6E22E"        # Monokai green — passing checks, shipped

  # Links — Monokai cyan + purple
  link: "#66D9EF"               # Monokai cyan — distinctive link signal
  link-visited: "#AE81FF"       # Monokai purple — visited body-text links
  link-hover: "#9EE5F5"         # lightened cyan for hover

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
  sm: 3px        # code-span, small pills
  md: 4px        # buttons, inputs
  lg: 6px        # cards, panels, larger surfaces
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

Monokai-inspired dark reading surface. Monokai is one of the most-recognized developer color schemes in the world — decades of refinement, immediately readable to anyone who has spent time in a code editor. The palette maps naturally to the information density cowork-render produces: vivid accent colors for severity signals, warm neutrals for body prose, and a distinctive cyan link color that stands apart from both heading and body text without feeling disconnected.

The background is anchored on Monokai's canonical `#272822` warm dark rather than pure or blue-shifted black. Surface lifts (`#3E3D32` for cards, `#49483E` for raised elements) follow Monokai's own layering logic. Every cowork-render output should feel like part of one family — same palette, same font choices, same spacing rhythm — whether the shape is a kanban, a dashboard, or a timeline.

## Colors

**Backgrounds** warm from `bg-base` (`#272822`, Monokai's canonical body) through `bg-surface` (`#3E3D32`) through `bg-surface-raised` (`#49483E`) through `bg-surface-hover` (`#5A594F`). Warm brown-gray tones rather than the blue-shifted dark common in GitHub-style themes. `bg-code` (`#1E1F1C`) sits slightly darker than `bg-base` for code-span and code-block contrast.

**Text** is anchored on Monokai cream (`#F8F8F2` for body and strong, `#FFFFFF` for headings). `text-muted` is `#ABA994` — a deliberate deviation from Monokai's original comment color (`#75715E`). Monokai's comment color is intentionally low-contrast in code editors (signaling "deemphasized"), but in body-text contexts it fails WCAG AA at ~4:1 on `bg-base`; `#ABA994` retains the warm-gray feel while passing AA at ~6.2:1. `text-code` uses Monokai green (`#A6E22E`) for inline code accents.

**Severity** maps to Monokai's five core accent colors: pink/magenta for high (`#F92672`), orange for medium (`#FD971F`), yellow for low (`#E6DB74`), comment gray for info (`#75715E`), and green for ok (`#A6E22E`). The ramp uses Monokai's actual accent values — not desaturated approximations — because against the warm dark background they read clearly without being garish.

**Links** use Monokai cyan (`#66D9EF`) as the primary link color. Cyan is distinctive from both heading white and body cream, and signals "interactive" in the same way it does in terminal output and code highlighting. Visited links shift to Monokai purple (`#AE81FF`) — the classic visited-link affordance in a color that fits the palette naturally. Hover lightens to `#9EE5F5`.

## Typography

Body in Georgia serif — readable for long-form prose, conveys document-rather-than-app feel. Body font size is 17px (bumped from 15px for comfortable reading in browser contexts), line-height 1.7.

**JetBrains Mono** leads the monospace stack, with Fira Code → SF Mono → Menlo → Consolas → generic monospace as fallbacks. JBM has strong readability characteristics at small sizes, excellent ligature support, and is common on developer workstations. The font must be installed system-wide to render — no WOFF2 bundle, no CDN fetch. The fallback chain degrades gracefully on machines without JBM; the system mono stack covers every environment. Mono size is 0.92em; meta/timestamp contexts use 0.85rem.

## Layout primitives

`rounded.sm` (3px) for inline code spans and small pills. `rounded.md` (4px) for buttons and inputs. `rounded.lg` (6px) for cards and panels. `rounded.pill` (999px) for status pills and count badges (full ellipse).

Spacing scale runs from `xs` (4px) through `xxl` (32px) on a roughly 1.5x ratio. Use `xs/sm` for tight inline contexts (badge padding, code-span padding), `md/lg` for card content, `xl/xxl` for section spacing.

## Do's and don'ts

**Do** consume colors and dimensions via CSS variables (`var(--bg-base)`, `var(--severity-high)`, etc.) — never hardcode hex values in renderer modules.

**Do** add new tokens here when a real renderer need arises that the existing palette doesn't cover. Update the CSS variables block automatically via the loader.

**Don't** import a renderer-specific palette inline. The whole point is consolidation.

**Don't** use the severity colors for non-severity purposes (e.g., decorative accents). They carry semantic weight; misuse dilutes the signal.

**Don't** add a light-mode variant in v1. Single Monokai dark theme is canonical.
