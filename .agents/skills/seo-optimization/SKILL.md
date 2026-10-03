---
name: seo-optimization
description: 'Comprehensive SEO engineering and technical search engine optimization for web applications and e-commerce platforms. Covers Google Search Central guidelines, meta tags, OpenGraph, Twitter Cards, Schema.org JSON-LD structured data (Product, Organization, LocalBusiness, BreadcrumbList, Article, WebSite), canonical URL strategy, XML Sitemap standards (W3C Datetime, Google Image sitemap), robots.txt rules, Core Web Vitals, and keyword optimization.'
---

# SEO Optimization Skill

This skill provides comprehensive technical search engine optimization (SEO) standards, architecture patterns, and auditing workflows for web applications and e-commerce platforms (Laravel Blade, React/Next.js, Vue).

---

## 1. Technical SEO Foundation

### 1.1 Canonical URL Strategy

- Every indexable page **must** declare a single self-referencing canonical URL:
    ```html
    <link rel="canonical" href="https://example.com/canonical-path" />
    ```
- Eliminate duplicate content variations (`/path/`, `/path?ref=...`, uppercase vs lowercase).
- Alias or deprecated URLs must issue an HTTP `301 Moved Permanently` redirect to the canonical URL, never serve duplicate content or daisy-chain redirects (`301 -> 301`).

### 1.2 Robots Meta Directives

- **Indexable pages:**
    ```html
    <meta
        name="robots"
        content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"
    />
    <meta
        name="googlebot"
        content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1"
    />
    ```
- **Internal/Admin/Draft/Private pages:**
    ```html
    <meta name="robots" content="noindex, nofollow" />
    ```
- HTTP Header alternative for XML/JSON feeds and downloads:
    ```http
    X-Robots-Tag: noindex, follow
    ```

---

## 2. On-Page Metadata & Social Sharing

### 2.1 Title & Description Standards

- **Title Tag:**
    - Length: 50–60 characters (pixel width ~580px).
    - Format: `[Primary Keyword / Page Subject] | [Brand Name]`
    - Unique across every single URL. Never allow duplicate titles across pages.
- **Meta Description:**
    - Length: 140–160 characters.
    - Action-oriented summary with value proposition, primary keywords, and clear call-to-action (CTA).
    - Escaped properly (no raw HTML tags or unescaped quotes).

### 2.2 Open Graph & Twitter Cards

```html
<!-- Open Graph / Facebook / Zalo -->
<meta property="og:type" content="website" />
<!-- or 'article', 'product' -->
<meta property="og:url" content="https://example.com/current-url" />
<meta property="og:title" content="Page Title | Brand Name" />
<meta property="og:description" content="Engaging 150-character summary." />
<meta property="og:image" content="https://example.com/images/og-image.jpg" />
<meta property="og:locale" content="vi_VN" />
<meta property="og:site_name" content="Brand Name" />

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Page Title | Brand Name" />
<meta name="twitter:description" content="Engaging 150-character summary." />
<meta name="twitter:image" content="https://example.com/images/og-image.jpg" />
```

---

## 3. Schema.org JSON-LD Structured Data

All schemas must use `<script type="application/ld+json">` and conform to Schema.org standards.

### 3.1 Organization & LocalBusiness (Global Layout)

```json
{
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": ["Organization", "LocalBusiness"],
            "@id": "https://example.com/#organization",
            "name": "Company Full Name",
            "url": "https://example.com",
            "logo": "https://example.com/images/logo.png",
            "telephone": "+84903846568",
            "email": "contact@example.com",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "Street Address",
                "addressLocality": "City / Province",
                "addressCountry": "VN"
            }
        },
        {
            "@type": "WebSite",
            "@id": "https://example.com/#website",
            "url": "https://example.com",
            "name": "Brand Name",
            "publisher": { "@id": "https://example.com/#organization" },
            "potentialAction": {
                "@type": "SearchAction",
                "target": {
                    "@type": "EntryPoint",
                    "urlTemplate": "https://example.com/search?q={search_term_string}"
                },
                "query-input": "required name=search_term_string"
            }
        }
    ]
}
```

### 3.2 Product Schema (Product Detail Pages)

```json
{
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "Product Name",
    "image": ["https://example.com/product.jpg"],
    "description": "Product detailed description without HTML tags.",
    "sku": "SKU-12345",
    "brand": {
        "@type": "Brand",
        "name": "Brand Name"
    },
    "offers": {
        "@type": "Offer",
        "url": "https://example.com/product-url",
        "priceCurrency": "VND",
        "price": "0",
        "availability": "https://schema.org/InStock",
        "seller": {
            "@type": "Organization",
            "name": "Brand Name"
        }
    }
}
```

### 3.3 BreadcrumbList Schema (Hierarchy Navigation)

```json
{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
        {
            "@type": "ListItem",
            "position": 1,
            "name": "Trang chủ",
            "item": "https://example.com"
        },
        {
            "@type": "ListItem",
            "position": 2,
            "name": "Danh mục",
            "item": "https://example.com/category"
        },
        {
            "@type": "ListItem",
            "position": 3,
            "name": "Tên sản phẩm",
            "item": "https://example.com/product-url"
        }
    ]
}
```

### 3.4 Article / NewsArticle Schema

```json
{
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "Article Title",
    "description": "Article summary",
    "image": ["https://example.com/news-thumb.jpg"],
    "datePublished": "2026-09-29T08:00:00+07:00",
    "dateModified": "2026-09-29T10:00:00+07:00",
    "author": {
        "@type": "Organization",
        "name": "Editorial Team"
    },
    "publisher": {
        "@type": "Organization",
        "name": "Brand Name",
        "logo": {
            "@type": "ImageObject",
            "url": "https://example.com/logo.png"
        }
    }
}
```

---

## 4. XML Sitemap Standards (Google & sitemaps.org)

1. **Protocol Specifications:**
    - Root tag: `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">`
    - Content-Type header: `Content-Type: application/xml; charset=utf-8`
    - Encoding: UTF-8 with XML entity escaping (`&` $\rightarrow$ `&amp;`, `'` $\rightarrow$ `&apos;`, `"` $\rightarrow$ `&quot;`, `<` $\rightarrow$ `&lt;`, `>` $\rightarrow$ `&gt;`).
2. **URL Eligibility Rules:**
    - Only return canonical, status `200 OK` indexable URLs.
    - Strictly exclude redirects (`301`/`302`), error pages (`404`/`500`), and `noindex` pages.
3. **Date Format (`<lastmod>`):**
    - Must be W3C Datetime (`YYYY-MM-DD` or `YYYY-MM-DDThh:mm:ss+00:00`).
    - Use actual entity modification timestamps (`updated_at`). Do NOT inject `$now` dynamically on every request for static pages.
4. **Google Image Sitemap Extension:**
    - Include `<image:image>` with `<image:loc>` and `<image:title>` for products and news articles to maximize Google Image Search rankings.
5. **Robots.txt integration:**
    - Link sitemap at the end of `robots.txt`:
        ```txt
        Sitemap: https://example.com/sitemap.xml
        ```

---

## 5. Semantic HTML & Content Architecture

1. **Single `<h1>` per page:**
    - Homepage: Company / Core Business Proposition.
    - Catalog: Category Name or "Tất cả sản phẩm".
    - Product Detail: Product Name.
    - News Detail: Article Title.
2. **Heading Hierarchy:**
    - Follow strict logical progression: `h1` $\rightarrow$ `h2` $\rightarrow$ `h3`.
    - Never skip heading levels for visual styling (use CSS classes instead).
3. **Image Optimization & Accessibility:**
    - All `<img>` tags must have descriptive `alt` text.
    - Include explicit `width` and `height` (or reserved aspect ratios) to eliminate Cumulative Layout Shift (CLS).
    - Set `loading="lazy"` on below-the-fold images, and `loading="eager"` + `fetchpriority="high"` on above-the-fold LCP hero images.
