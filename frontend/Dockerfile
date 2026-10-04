# Stage 1: Build React Vite SPA using pnpm monorepo workspace
FROM node:22-alpine AS builder

WORKDIR /app

RUN npm install -g pnpm@11.20.0

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY frontend/package.json ./frontend/

RUN pnpm install --frozen-lockfile

COPY frontend ./frontend

ARG VITE_API_BASE_URL="/api/v1"
ARG VITE_DEMO_REPORT_DATE="2026-09-01"
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_DEMO_REPORT_DATE=$VITE_DEMO_REPORT_DATE

RUN pnpm --filter mco-frontend build

# Stage 2: Serve with Nginx
FROM nginx:1.27-alpine AS runtime

COPY --from=builder /app/frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
