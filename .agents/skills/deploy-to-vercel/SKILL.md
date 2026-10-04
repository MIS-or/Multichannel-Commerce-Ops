---
name: deploy-to-vercel
description: |
    End-to-end Vercel deployment automation and configuration.
    Covers vercel.json setup, build settings, environment variables, routing rewrites,
    serverless/edge functions, and preview/production deployment validation.

    Relevant when:
      - Preparing a project for deployment to Vercel.
      - Creating or configuring vercel.json (headers, rewrites, redirects, caching).
      - Troubleshooting Vercel build failures or deployment runtime errors.
---

# Deploy to Vercel

Complete guide and configuration standards for deploying modern web applications to Vercel with zero downtime and optimal edge performance.

---

## 1. Framework Build Configurations

| Framework              | Output Directory    | Build Command   | Development Command |
| :--------------------- | :------------------ | :-------------- | :------------------ |
| **Vite (React / Vue)** | `dist`              | `npm run build` | `npm run dev`       |
| **Next.js**            | `.next` (Automatic) | `next build`    | `next dev`          |
| **Astro**              | `dist`              | `astro build`   | `astro dev`         |
| **SvelteKit**          | `.svelte-kit`       | `vite build`    | `vite dev`          |

---

## 2. Production `vercel.json` Configuration

For Single Page Applications (Vite / React Router) with security headers:

```json
{
    "$schema": "https://openapi.vercel.sh/vercel.json",
    "rewrites": [
        {
            "source": "/(.*)",
            "destination": "/index.html"
        }
    ],
    "headers": [
        {
            "source": "/assets/(.*)",
            "headers": [
                {
                    "key": "Cache-Control",
                    "value": "public, max-age=31536000, immutable"
                }
            ]
        },
        {
            "source": "/(.*)",
            "headers": [
                {
                    "key": "X-Content-Type-Options",
                    "value": "nosniff"
                },
                {
                    "key": "X-Frame-Options",
                    "value": "DENY"
                },
                {
                    "key": "X-XSS-Protection",
                    "value": "1; mode=block"
                },
                {
                    "key": "Referrer-Policy",
                    "value": "strict-origin-when-cross-origin"
                }
            ]
        }
    ]
}
```

---

## 3. Deployment Checklist

1. **Verify Local Build**: Run `npm run build` and ensure zero compilation or type errors.
2. **Environment Variables**:
    - Ensure all client-facing variables use appropriate prefixes (e.g. `VITE_` or `NEXT_PUBLIC_`).
    - Create `.env.example` documenting every required variable.
    - Do NOT commit `.env` or secrets to Git.
3. **Deploy via CLI**:
    - Preview deployment: `npx vercel`
    - Production deployment: `npx vercel --prod`
