---
name: ui-ux-pro-max
description: |
    Comprehensive UI/UX design intelligence system for crafting world-class, premium user interfaces.
    Provides design tokens, curated color systems, modern typography, layout patterns (Bento grid,
    glassmorphism, sleek dark mode), micro-interactions, responsive design rules, and WCAG accessibility.

    Relevant when:
      - Designing or building any frontend web or mobile interface (HTML/CSS, React, Next.js, Vue, Tailwind).
      - Modernizing an outdated or basic user interface into a stunning, premium experience.
      - Establishing a design system (color palettes, font pairings, spacing scales, shadow tokens).
      - Reviewing UI for responsive design, micro-animations, and UX heuristics.
---

# UI/UX Pro Max: Design Intelligence System

UI/UX Pro Max turns any standard interface into an exceptional, production-grade product that delights users at first glance.

---

## 1. Design Aesthetics & Visual Polish

### Avoid Generic Looks

- **Never use generic primary colors** (`#ff0000`, `#0000ff`, `#00ff00`). Always use curated HSL/HEX palettes.
- **Deep Sleek Dark Mode**: Avoid pure black (`#000000`) for surfaces. Use layered dark tones:
    - Background base: `#090A0F` or `#0F172A` (Slate 900)
    - Card/Surface level 1: `#151B2B` or `#1E293B`
    - Border/Divider: `rgba(255, 255, 255, 0.08)` to `rgba(255, 255, 255, 0.12)`
    - Primary accent: Vibrantly tuned indigo (`#6366F1`), violet (`#8B5CF6`), or emerald (`#10B981`).
- **Glassmorphism**:
    - `background: rgba(255, 255, 255, 0.04);`
    - `backdrop-filter: blur(12px);`
    - `border: 1px solid rgba(255, 255, 255, 0.08);`
    - `box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);`

---

## 2. Typography Hierarchy

Use Google Fonts with proven modern readability:

- **Display / Headers**: _Outfit_, _Plus Jakarta Sans_, _Cabinet Grotesk_, or _Syne_.
- **Body / Interface**: _Inter_, _Geist_, _DM Sans_, or _Roboto_.
- **Code / Monospace**: _JetBrains Mono_ or _Fira Code_.

### Fluid Typography Scale

```css
:root {
    --font-display: 'Plus Jakarta Sans', system-ui, sans-serif;
    --font-body: 'Inter', system-ui, sans-serif;
    --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.8125rem);
    --text-sm: clamp(0.875rem, 0.8rem + 0.35vw, 0.9375rem);
    --text-base: clamp(1rem, 0.95rem + 0.25vw, 1.0625rem);
    --text-lg: clamp(1.125rem, 1.05rem + 0.4vw, 1.25rem);
    --text-xl: clamp(1.25rem, 1.15rem + 0.5vw, 1.5rem);
    --text-2xl: clamp(1.5rem, 1.3rem + 1vw, 2rem);
    --text-3xl: clamp(2rem, 1.7rem + 1.5vw, 2.75rem);
}
```

---

## 3. Modern Layout Patterns

### Bento Grid

- Organize dashboard, landing page features, and content modules using asymmetric Bento Grids.
- Give hero items `col-span-2` or `row-span-2`.
- Every card must feature an icon, clean badge/pill, clear title, concise descriptive copy, and an optional micro-preview or metric graph.

### Interactive Micro-Animations

- **Hover Transitions**: `transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);`
- **Card Lift**: `transform: translateY(-3px); box-shadow: 0 12px 24px -10px rgba(0,0,0,0.4);`
- **Button Shimmer / Glow**: Subtle gradient animation or radial glow following the cursor.
- **Empty States & Skeletons**: Always provide skeleton loaders instead of jarring layout shifts or empty spinners.

---

## 4. UX Heuristics & Usability Checklist

1. **Touch Targets**: Minimum `44px x 44px` on all buttons, links, and interactive elements.
2. **Immediate Feedback**: Hover states, active/press states, loading spinners on submit buttons, and toast notifications.
3. **Contrast & Accessibility (WCAG 2.1 AA)**:
    - Minimum contrast ratio 4.5:1 for regular text, 3:1 for large text.
    - Visible keyboard focus rings: `outline: 2px solid var(--accent); outline-offset: 2px;`
4. **Responsive Breakpoints**:
    - Mobile: `< 640px` (Single column, bottom navigation or drawer)
    - Tablet: `640px - 1024px` (2 columns, collapsible sidebar)
    - Desktop: `> 1024px` (Full multi-column layout, persistent navigation)
