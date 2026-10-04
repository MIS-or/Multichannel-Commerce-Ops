# Multichannel Commerce Operations (MCO)

> **Multichannel Commerce Integration, Reconciliation & Automation Platform**

MCO is an enterprise-grade internal operations platform for multichannel commerce. It connects external business systems (ERPs, Marketplaces, WMS, Payment Gateways), normalizes and validates operational data, performs automated multi-dimensional reconciliation (settlements and inventory), detects operational exceptions, and automates supervised workflows.

The project is architected as a **hardened Modular Monolith**: FastAPI owns domain business rules, public module facades, and ACID transactions; PostgreSQL provides durable ACID isolation; n8n manages schedules and transport orchestration; and React provides a typed, component-driven dashboard.

---

## What V1 Proves

- **Deterministic Multi-Platform Mock Feeds**: Shopee, TikTok Shop, and Direct Website.
- **Idempotent Ingestion**: Uniquely identified by `(channel_id, external_order_id)`. Re-imports are safe no-ops.
- **ACID Transaction Boundary**: Single atomic transaction encompasses order ingestion, item rows, stock decrement, ledger entries, and low-stock alerts.
- **Concurrency-Safe Stock Consumption**: Atomic conditional SQL decrement (`WHERE current_stock >= :quantity RETURNING products`) prevents overselling.
- **Durable Historical Financials**: Historical COGS preserved via `order_items.unit_cost` snapshots; double-entry ledger records revenue and COGS.
- **Machine-Enforced Modular Monolith Boundaries**: AST linter (`scripts/check_module_boundaries.py`) verifies encapsulation and prevents architectural drift.
- **Decoupled Module Contracts**: Inter-module calls exchange focused DTO schemas (`OrderSaleRecord`, `LowStockAlertRequest`) rather than foreign ORM entities.
- **Daily Multi-Channel Reporting**: Read-only aggregation model reporting gross profit, revenue, and COGS across all channels.
- **Automated Financial Reconciliation**: Channel settlement logs checked against internal orders and ledger entries.
- **Deduplicated Alert Dispatch**: Operations alerts with delivery state tracking.
- **PostgreSQL Critical-Path Integration**: Full commerce lifecycle integration tests verified under real PostgreSQL engine semantics.
- **Modern React/Vite Operations Dashboard**: React 19, TypeScript, Tailwind CSS, TanStack Query, and Vitest.

---

## System Architecture

```text
Shopee Mock  ----\
TikTok Mock   ----> [n8n Orchestrator] ----> [FastAPI Modular Monolith] ----> [PostgreSQL]
Website Mock ----/                                   |    |
                                                     |    +----> alerts ----> n8n ----> Telegram
                                                     |
[React 19 / Vite Operations UI] <--------------------+
```

Editable architecture package: [`docs/architecture/MCO_Architecture_Specification.drawio`](docs/architecture/MCO_Architecture_Specification.drawio).

### Modular Monolith Bounded Contexts

The backend is structured into isolated bounded contexts under `backend/app/modules/`:

| Module | Responsibility | Public Facade Surface |
| :--- | :--- | :--- |
| **`alerts`** | Operational alerting, deduplication, resolution | `Alert`, `AlertService`, `LowStockAlertRequest`, `router` |
| **`channels`** | Sales channels configuration and registry | `Channel`, `ChannelService`, `get_channel_service` |
| **`inventory`** | Stock levels and atomic decrement operations | `InventoryService`, `InventoryItemRead`, `router` |
| **`ledger`** | Financial double-entry revenue/COGS journal | `LedgerEntry`, `LedgerService`, `OrderSaleRecord` |
| **`mock_channels`**| Mock channel feeds for development/demo | `MockChannelService`, `MockOrderFeed`, `router` |
| **`orders`** | Ingestion pipeline, idempotency, order query | `Order`, `OrderService`, `OrderImportRequest`, `router` |
| **`products`** | Catalog master data and SKU specifications | `Product`, `ProductService`, `get_product_service` |
| **`reconciliation`**| Channel settlement audit and mismatch detection| `ReconciliationService`, `ReconciliationRequest`, `router` |
| **`reports`** | Cross-channel analytics read model (ADR-001) | `ReportsService`, `DailyReport`, `router` |

### Architectural Boundary Rules

1. **Public Facade Pattern (`__all__`)**: Every module exposes its public API through its top-level `__init__.py`.
2. **Repository Encapsulation**: Repositories are strictly private persistence adapters. Repositories must **never** be exported from module facades or imported across module boundaries.
3. **Read-Model Aggregation Exception (ADR-001)**: The `reports` module is the single permitted architectural exception allowed to perform cross-domain read-only SQL queries joining tables directly.
4. **Inter-Module DTO Contracts (ADR-008)**: Cross-module service calls must pass minimal, explicit Pydantic DTOs (e.g. `OrderSaleRecord`) rather than foreign ORM entities.
5. **Automated AST Enforcement**: Checked automatically via `scripts/check_module_boundaries.py` during `make check` and CI.

---

## Automation Workflows (n8n)

Workflows located in [`n8n/workflows/`](n8n/workflows/) provide lightweight schedule and transport orchestration. They dictate **when** processes run and route data between external endpoints; FastAPI remains the sole authority for business logic, ACID transactions, inventory decrements, accounting, and reconciliation.

| Workflow | Cadence | Responsibility |
| :--- | :--- | :--- |
| **`order-sync.json`** | Every 15 min | Fetches deterministic channel feeds, normalizes payloads, and calls the idempotent order import API (`POST /api/v1/orders/import`). |
| **`reconciliation.json`** | Every 6 hours | Extracts source snapshot settlements and submits them to the reconciliation engine (`POST /api/v1/reconciliations`). |
| **`alert-notification.json`** | Every 5 min | Polls pending operational alerts (`GET /api/v1/alerts/pending-notifications`) and dispatches notifications to Telegram. |

### Environment Variables & Secrets
- `MCO_API_BASE_URL`: Backend origin, e.g. `http://host.docker.internal:8000`.
- `TELEGRAM_BOT_TOKEN`: Required only by the alert-delivery workflow.
- `TELEGRAM_CHAT_ID`: Required only by the alert-delivery workflow.

### Failure Policy & Delivery Semantics
- **Idempotent Ingestion Retries**: All external import calls are protected by `(channel_id, external_order_id)` unique constraints; duplicate imports safely return a `DUPLICATE` status without duplicate side effects.
- **At-Least-Once Alert Delivery**: The notification workflow marks `notified_at` via `PATCH /api/v1/alerts/{id}/notified` only after Telegram confirms message receipt. If an execution fails before the marker is persisted, the alert remains pending for the next scheduled run.

---

## Infrastructure & Local Stack

The compose setup in [`infra/docker-compose.yml`](infra/docker-compose.yml) provides a fully integrated local environment maintaining a strict startup sequence:

```text
PostgreSQL healthy -> migrations -> demo seed -> FastAPI healthy -> n8n
```

This sequence prevents the API from serving against an unapplied schema and ensures all mock data is seeded before n8n triggers scheduled synchronization runs.

### Production Topology Boundary
- **Database**: Managed PostgreSQL (e.g. Neon) using `MCO_DATABASE_URL` (asyncpg pooled) and `MCO_MIGRATION_DATABASE_URL` (direct psycopg for Alembic).
- **Backend**: FastAPI containerized deployment (e.g. Railway).
- **Frontend**: Static SPA deployment (e.g. Cloudflare Pages).
- **Automation**: Separately secured, authenticated n8n deployment with stable `N8N_ENCRYPTION_KEY`. Pinned to `2.38.2` with `vm` expression engine.

---

## Development Workflows

### Option A: Local Non-Docker Development

#### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows: .venv\Scripts\activate; On Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"

# Run database migrations and demo seed (SQLite or local PostgreSQL)
alembic upgrade head
python -m app.scripts.seed_demo

# Start the development server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
pnpm install
pnpm run dev
```

Default URLs:
- API & Docs: `http://localhost:8000/docs`
- Health Checks: `http://localhost:8000/health`, `http://localhost:8000/ready`
- Dashboard: `http://localhost:5173`

---

### Option B: Docker Compose Full-Stack

To spin up the complete integrated stack (Frontend, Backend, PostgreSQL, Migrations, Seed, and n8n):
```bash
cp .env.example .env
docker compose up -d --build
```

Services:
- Operations Dashboard: `http://localhost:5173`
- Backend API & Docs: `http://localhost:8000/docs`
- n8n Automation: `http://localhost:5678`
- PostgreSQL: `localhost:5432`

---

## Quality Gates & Verification

All quality gates must pass cleanly before any code is merged:

```bash
# Run the complete verification suite across backend, frontend, boundaries, and artifacts:
make check
```

Or run individual verification commands:

| Scope | Command | Purpose |
| :--- | :--- | :--- |
| **Architecture** | `python scripts/check_module_boundaries.py` | AST boundary linter verifying module encapsulation |
| **Backend Lint** | `cd backend && ruff check app tests` | Enforces code style, bug patterns, and import conventions |
| **Type Safety** | `cd backend && mypy app` | Strict static typing across all modules |
| **Unit & Integration** | `cd backend && pytest` | 40+ unit, boundary, and transaction integrity tests |
| **PostgreSQL Integration** | `cd backend && pytest tests/integration/test_postgres_commerce_pipeline.py` | Validates commerce pipeline on PostgreSQL engine |
| **Frontend Lint** | `pnpm --filter mco-frontend lint` | ESLint rules across UI components |
| **Frontend Tests**| `pnpm --filter mco-frontend test` | Vitest component and logic tests |
| **Frontend Build**| `pnpm --filter mco-frontend build` | Production bundle compilation check |
| **Artifacts** | `python scripts/validate_artifacts.py` | Validates n8n workflows and draw.io architecture XML |

---

## Documentation Index

- [`CONTRIBUTING.md`](CONTRIBUTING.md): Branching, commits, PR guidelines, and boundary rules.
- [`docs/runbook.md`](docs/runbook.md): Operational procedures, deployment, and incident management.
- [`docs/api/contracts.md`](docs/api/contracts.md): Complete OpenAPI endpoint specifications.
- [`docs/adr/`](docs/adr/): Architecture Decision Records:
  - `001-modular-monolith.md`: Modular monolith architecture.
  - `002-n8n-orchestration.md`: Orchestration boundaries.
  - `003-order-idempotency.md`: Idempotency keys and deduplication.
  - `004-order-transaction-boundary.md`: Single ACID transaction boundary.
  - `005-react-vite-frontend.md`: Frontend technology stack.
  - `006-paid-orders-v1.md`: Scope boundaries for V1 orders.
  - `007-modular-monolith-boundaries.md`: Strict service encapsulation and repository privacy.
  - `008-inter-module-dto-contracts.md`: Inter-module DTO contract decoupling.
  - `009-public-facade-pattern.md`: Public facades (`__all__`) and AST linter enforcement.
