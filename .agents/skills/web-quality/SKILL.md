---
name: web-quality
description: |
    Comprehensive web quality assurance engineering.
    Ensures Core Web Vitals optimization, semantic HTML5 structure, WCAG 2.1 AA accessibility,
    SEO metadata (OpenGraph, Twitter Cards, JSON-LD schema), and security headers.

    Relevant when:
      - Auditing or optimizing web performance and Core Web Vitals (LCP, FID/INP, CLS).
      - Implementing SEO, social sharing cards, and structured schema data.
      - Ensuring accessibility compliance (ARIA, keyboard navigation, contrast).
      - Hardening web security (CSP, HTTPS, input sanitization).
---

# Web Quality Engineering

Deliver production-grade web applications that achieve 95+ scores on Lighthouse: blazing performance, full accessibility, bulletproof SEO, and clean security hygiene.

---

## 1. Core Web Vitals Thresholds

| Metric                              | Target (Good) | Strategy                                                                                                     |
| :---------------------------------- | :------------ | :----------------------------------------------------------------------------------------------------------- |
| **LCP** (Largest Contentful Paint)  | **< 2.5s**    | Preload hero fonts/images, avoid render-blocking CSS, compress assets with WebP/AVIF.                        |
| **INP** (Interaction to Next Paint) | **< 200ms**   | Debounce event handlers, yield to main thread with `scheduler.yield()` or `requestIdleCallback`.             |
| **CLS** (Cumulative Layout Shift)   | **< 0.1**     | Explicit `width` and `height` on all `<img>` and `<video>`, reserve container space with CSS `aspect-ratio`. |

---

## 2. Semantic HTML & Accessibility (WCAG 2.1 AA)

- **Semantic Landmarks**:
    - Always use `<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<aside>`, and `<footer>`.
    - Only one `<h1>` element per page.
- **Keyboard Navigation**:
    - All interactive elements must be focusable via `Tab`.
    - Never set `outline: none` without a visible `:focus-visible` replacement.
- **Images & Icons**:
    - Meaningful images must have descriptive `alt` text.
    - Decorative icons must have `aria-hidden="true"`.
- **Form Controls**:
    - Every `<input>` must have an associated `<label for="...">` or `aria-label`.

---

## 3. Complete SEO & Social Meta Checklist

Add to `<head>` for maximum discoverability:

```html
<!-- Primary Meta Tags -->
<title>Product Name - Clear Value Proposition</title>
<meta name="title" content="Product Name - Clear Value Proposition" />
<meta
    name="description"
    content="Engaging 150-160 character description summarizing the application."
/>
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<link rel="canonical" href="https://yourdomain.com/" />

<!-- Open Graph / Facebook / LinkedIn -->
<meta property="og:type" content="website" />
<meta property="og:url" content="https://yourdomain.com/" />
<meta property="og:title" content="Product Name - Clear Value Proposition" />
<meta
    property="og:description"
    content="Engaging 150-160 character description."
/>
<meta property="og:image" content="https://yourdomain.com/og-image.png" />

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Product Name - Clear Value Proposition" />
<meta
    name="twitter:description"
    content="Engaging 150-160 character description."
/>
<meta name="twitter:image" content="https://yourdomain.com/og-image.png" />
```
