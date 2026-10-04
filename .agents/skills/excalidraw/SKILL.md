---
name: excalidraw
description: |
    Visual architecture, system design, and workflow diagramming.
    Designs clear system architectures, database ERDs, user flows, and wireframes
    using Excalidraw formats and Mermaid visual specifications.

    Relevant when:
      - Visualizing system architecture, microservices, or database schemas.
      - Designing user journey flows, API sequences, and data pipelines.
      - Generating UI wireframes and component hierarchies.
---

# Excalidraw & System Architecture Diagramming

A great diagram communicates complex architectures in seconds. Use visual hierarchy, consistent color layers, and clear data flows.

---

## 1. Architectural Color Layering

When diagramming systems or wireframes, use standardized semantic colors:

| Layer                     | Semantic Role                     | Excalidraw / Hex Color              |
| :------------------------ | :-------------------------------- | :---------------------------------- |
| **Client / Frontend**     | Web App, Mobile App, Browser      | `#3B82F6` (Blue) / `#06B6D4` (Cyan) |
| **API Gateway / Proxy**   | Reverse Proxy, Rate Limiter, Auth | `#6366F1` (Indigo)                  |
| **Services / Workers**    | Business Logic, Background Jobs   | `#8B5CF6` (Purple)                  |
| **Database & Cache**      | PostgreSQL, Redis, Storage        | `#10B981` (Emerald)                 |
| **External Integrations** | Stripe, SendGrid, AI APIs         | `#F59E0B` (Amber)                   |

---

## 2. Mermaid Diagram Formats

Antigravity natively renders Mermaid diagrams in markdown artifacts. Use these standard formats:

### System Architecture Flowchart

```mermaid
flowchart TD
    Client["🌐 Client (React/Vite)"]
    Gateway["🛡️ API Gateway / Auth"]
    Service["⚙️ Core Backend Service"]
    DB[("🗄️ PostgreSQL Database")]
    Cache[("⚡ Redis Cache")]

    Client -->|HTTPS / JSON| Gateway
    Gateway --> Service
    Service --> Cache
    Service --> DB
```

### Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend
    participant Backend
    participant DB

    User->>Frontend: Click "Submit Order"
    Frontend->>Backend: POST /api/orders
    Backend->>DB: INSERT order (Transaction)
    DB-->>Backend: Order ID: #1084
    Backend-->>Frontend: 201 Created { id, status }
    Frontend-->>User: Display Success Toast
```
