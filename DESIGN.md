---
name: cowork-render dark
version: alpha
description: Canonical visual identity for every renderer cowork-render produces (kanban, dashboard, timeline, future shapes). Source of truth — every renderer consumes this via cowork_render.theme.

colors:
  # Backgrounds — lightest to darkest tint
  bg-base: "#16161a"           # body background, near-black
  bg-surface: "#1f2128"        # card/panel surface, subtle lift
  bg-surface-raised: "#25272e" # column headers, raised UI elements
  bg-surface-hover: "#2a2c33"  # hover state
  bg-code: "#16161a"           # code-span and code-block background
  bg-input: "#1f2128"          # input field background

  # Text
  text-base: "#e1e4e8"         # body text
  text-heading: "#f0f3f6"      # heading text
  text-muted: "#8b949e"        # meta lines, "no findings" copy, footers
  text-strong: "#c9d1d9"       # subsection headings, secondary headings
  text-code: "#79c0ff"         # inline code text color

  # Borders
  border-subtle: "#2d3138"     # card borders, hr separators
  border-emphasis: "#3a3f47"   # focused/emphasized borders

  # Severity ramp — used for finding cards, status pills, badge backgrounds
  severity-high: "#f85149"     # red — broken_links in active docs, errors
  severity-medium: "#e3b341"   # orange — ghost projects, hub inconsistencies
  severity-low: "#d29922"      # yellow — tag drift, stale docs
  severity-info: "#8b949e"     # gray — orphan docs, one-way edges
  severity-ok: "#3fb950"       # green — passing checks, shipped status

  # Links
  link: "#58a6ff"              # default link color
  link-visited: "#a371f7"      # visited link color (where contextually appropriate)
  link-hover: "#79b8ff"        # link hover state

typography:
  body:
    fontFamily: Georgia, 'Times New Roman', serif
    fontSize: 15px
    lineHeight: 1.65
  heading:
    fontFamily: Georgia, 'Times New Roman', serif
    fontWeight: 600
  mono:
    fontFamily: "'SF Mono', Menlo, Consolas, monospace"
    fontSize: 0.85em
  meta:
    fontFamily: "'SF Mono', Menlo, Consolas, monospace"
    fontSize: 0.78rem
  card-title:
    fontFamily: Georgia, 'Times New Roman', serif
    fontSize: 0.95rem
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

Dark-themed reading surface inspired by GitHub's dark mode and IDE-dark conventions. The visual identity is calm — high contrast where it matters (severity badges, headings), muted where it doesn't (body text, meta lines, footers). Every cowork-render output should feel like part of one family even when the shape (kanban, dashboard, timeline) differs.

The palette is anchored on near-black `#16161a` rather than pure black to reduce eye strain in long reading sessions, with subtle surface lifts (`#1f2128` for cards, `#25272e` for raised elements) that give visual hierarchy without screaming.

## Colors

The palette is rooted in three layers — backgrounds, text, severity — plus links.

**Backgrounds** ramp from `bg-base` (body) through `bg-surface` (cards) through `bg-surface-raised` (headers) through `bg-surface-hover` (interactive states). Each step lightens by a hair so visual hierarchy reads without explicit borders.

**Text** has four roles: `text-base` (body prose), `text-heading` (h1/h2/h3 in renderer chrome), `text-muted` (meta lines, footers, secondary information), `text-strong` (subsection headings, intermediate emphasis between heading and body). `text-code` is the inline-code accent — a soft blue (`#79c0ff`) that's distinct from links but signals "this is technical content."

**Severity** uses a five-tier ramp from `severity-high` (red, real problems demanding attention) down through `severity-medium`, `severity-low`, `severity-info`, ending at `severity-ok` (green, passing state). The colors are deliberately desaturated for dark-bg legibility — not pure red/orange/yellow/green. Used for finding cards in audit, status pills in dashboard, optional tag pills in timeline.

**Links** carry the visited distinction (purple `link-visited`) for body-text contexts where "have I read this" is useful information. UI-element links (count pills, badges) override visited to keep their saturated background contrast intact — that's a renderer-side concern, not a palette concern.

## Typography

Body in Georgia serif — readable for long-form prose, conveys document-rather-than-app feel. Mono in SF Mono / Menlo / Consolas stack for code, paths, dates, anything where character alignment matters. Card titles stay in body font (Georgia) at slightly smaller size — they're not headings, they're labels.

## Layout primitives

`rounded.sm` (3px) for inline code spans and small pills. `rounded.md` (4px) for buttons and inputs. `rounded.lg` (6px) for cards and panels. `rounded.pill` (999px) for status pills and count badges (full ellipse).

Spacing scale runs from `xs` (4px) through `xxl` (32px) on a roughly 1.5x ratio. Use `xs/sm` for tight inline contexts (badge padding, code-span padding), `md/lg` for card content, `xl/xxl` for section spacing.

## Do's and don'ts

**Do** consume colors and dimensions via CSS variables (`var(--bg-base)`, `var(--severity-high)`, etc.) — never hardcode hex values in renderer modules.

**Do** add new tokens here when a real renderer need arises that the existing palette doesn't cover. Update the CSS variables block automatically via the loader.

**Don't** import a renderer-specific palette inline. The whole point is consolidation.

**Don't** use the severity colors for non-severity purposes (e.g., decorative accents). They carry semantic weight; misuse dilutes the signal.

**Don't** add a light-mode variant in v1. Single dark theme is the canonical appearance.
