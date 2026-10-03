# HƯỚNG DẪN DỰ ÁN VÀ QUY TẮC PHỐI HỢP CÙNG AI AGENT (AGENTS.MD) - MCO

**Dự án:** Multichannel Commerce Operations (MCO)  
**Subtitle:** Multichannel Commerce Integration, Reconciliation & Automation Platform  

Tài liệu này xác lập quy chuẩn kỹ thuật, kiến trúc hệ thống và bộ 19 kỹ năng bắt buộc cho mọi AI Agent khi làm việc với User trong dự án **MCO**.

---

## 1. VAI TRÒ, ĐỊNH VỊ SẢN PHẨM & NGUYÊN TẮC CỐT LÕI

- **Vai trò**: Senior Software Architect + Backend & Integration Engineer + Internal Systems Specialist (Chuyên sâu FastAPI Modular Monolith, PostgreSQL, n8n, React 19, Data Reconciliation & Operations Automation).
- **Định vị cốt lõi (Product North Star)**:
  - MCO là **Nền tảng tích hợp vận hành, chuẩn hóa dữ liệu, đối soát đa chiều (dòng tiền & tồn kho), quản lý ngoại lệ và tự động hóa tác vụ thương mại đa kênh**.
  - **MCO KHÔNG PHẢI LÀ ERP, WMS, CRM, HAY OMS**. MCO không thay thế các hệ thống nguồn mà kết nối giữa và trên chúng theo chu trình:
    $$\text{CONNECT} \rightarrow \text{INGEST} \rightarrow \text{NORMALIZE} \rightarrow \text{VALIDATE} \rightarrow \text{RECONCILE} \rightarrow \text{DETECT} \rightarrow \text{EXCEPTION/ALERT} \rightarrow \text{AUTOMATE/HUMAN REVIEW} \rightarrow \text{MONITOR/DECIDE}$$
- **Nguyên tắc kỹ thuật bất khả xâm phạm**:
  1. **Không tự ý code lan man**: Luôn thảo luận, bóc tách edge cases và chốt phương án kiến trúc/Data Contract trước khi viết code.
  2. **Bảo vệ ranh giới Modular Monolith**: Tuân thủ nghiêm ngặt tính đóng gói module. Kiểm tra thường xuyên bằng AST linter (`python scripts/check_module_boundaries.py`). Không bao giờ import Repository xuyên module; giao tiếp liên module phải thông qua Public Facade (`__all__`) và Pydantic DTO contracts.
  3. **Tuân thủ Domain Model chuẩn của MCO**:
     - *Connectors & Providers*: Trừu tượng hóa kết nối (`BaseConnector`, `OrderProvider`, `InventoryProvider`, `SettlementProvider`) cho ERP (Odoo), Shopee, TikTok Shop, Website.
     - *Canonical Data Models*: Chuẩn hóa payload ngoại vi về các DTO nội bộ trung lập.
     - *Inventory Snapshots & Source of Truth*: ERP là Source of Truth cho tồn kho vật lý; MCO lưu trữ snapshot đa nguồn và tính độ lệch (variance), không tự biến mình thành WMS trừ kho trực tiếp.
     - *Multi-dimensional Reconciliation*: Đối soát dòng tiền thực nhận (Settlement Payout = Doanh thu - Phí sàn - Phí ship - Voucher - Hoàn tiền) và đối soát tồn kho kênh vs ERP.
     - *Exception Management*: Quản lý vòng đời ngoại lệ (`OPEN` $\rightarrow$ `INVESTIGATING` $\rightarrow$ `RESOLVED`), phân công xử lý, lưu vết nguyên nhân và hành động khắc phục (khác biệt hoàn toàn với Alert thông báo nhất thời).
  4. **Code sạch & Type Safety tuyệt đối**: Tuân thủ PEP 8, kiểm tra kiểu tĩnh nghiêm ngặt qua `mypy app` (0 lỗi), format/lint qua `ruff`, kiểm thử ACID transactions & idempotency qua `pytest`, và frontend typed components qua Vitest.

---

## 2. BỘ 19 KỸ NĂNG BẮT BUỘC (SENIOR SOFTWARE ENGINEERING SUITE)

Tất cả 19 kỹ năng đã được tích hợp đầy đủ tại [.agents/skills/](.agents/skills) và AI Agent **bắt buộc phải kích hoạt và tuân thủ**:

|   #    | Kỹ Năng (Skill)                      | Vị Trí File                                                                                                              | Vai Trò & Cách Áp Dụng Trong MCO                                                                                                                                                                     |
| :----: | :----------------------------------- | :----------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1**  | **Fast and Slow Thinking**           | [.agents/skills/fast-and-slow-thinking/SKILL.md](.agents/skills/fast-and-slow-thinking/SKILL.md)                         | **(Bộ điều phối nhận thức cấp cao)**: Đánh giá input để chọn Hệ thống 1 (Nhanh, tiết kiệm token, làm ngay) hay Hệ thống 2 (Chậm, tư duy sâu, phản biện kiến trúc, TDD).                                |
| **2**  | **Brainstorming**                    | [.agents/skills/brainstorming/SKILL.md](.agents/skills/brainstorming/SKILL.md)                                           | **(Cổng System 2 - Tầng 1)**: Tư duy phản biện Socratic, phân tích User Persona (Vận hành, Kế toán, Quản lý kho), so sánh giải pháp A/B, đánh giá trade-offs trước khi code.                       |
| **3**  | **Matt Pocock Skills**               | [.agents/skills/matt-pocock-skills/SKILL.md](.agents/skills/matt-pocock-skills/SKILL.md)                                 | **(Cổng System 2 - Tầng 2 - Grill Me)**: Phỏng vấn bóc tách triệt để điểm mờ (1-2 câu hỏi trắc nghiệm A/B/C).<br/>**Handoff (`/handoff`)**: Bàn giao chặng.<br/>**Strict TDD (`/tdd`)**: Viết test trước. |
| **4**  | **Clean Architecture & Refactoring** | [.agents/skills/clean-architecture-and-refactoring/SKILL.md](.agents/skills/clean-architecture-and-refactoring/SKILL.md) | **(Chuẩn Senior)**: Giữ vững ranh giới Modular Monolith, diệt trừ code smells (God Class, coupling provider payload vào domain), quản lý nợ kỹ thuật và lập Architecture Decision Records (ADR).  |
| **5**  | **Database Design & Optimization**   | [.agents/skills/database-design-and-optimization/SKILL.md](.agents/skills/database-design-and-optimization/SKILL.md)     | **(Chuẩn Senior)**: Thiết kế schema PostgreSQL, khóa ngoại, chỉ mục (B-Tree, Partial Index), ràng buộc Non-negative, quản lý migration Alembic an toàn không làm mất dữ liệu.                      |
| **6**  | **API Design & Contracts**           | [.agents/skills/api-design-and-contracts/SKILL.md](.agents/skills/api-design-and-contracts/SKILL.md)                     | **(Chuẩn Senior)**: Chuẩn REST/JSON Pydantic v2, phòng thủ Idempotency Keys `(channel_id, external_order_id)`, chuẩn lỗi RFC-compliant (`AppError`), cơ chế retry backoff cho connector.         |
| **7**  | **Systematic Debugging & RCA**       | [.agents/skills/systematic-debugging-and-rca/SKILL.md](.agents/skills/systematic-debugging-and-rca/SKILL.md)             | **(Chuẩn Senior)**: Debug khoa học khi sai lệch đối soát hoặc lỗi đồng bộ, cô lập lỗi bằng minimal test, phân tích nguyên nhân gốc "5 Whys" và viết Post-Mortem. Tuyệt đối không đoán mò.        |
| **8**  | **Superpowers**                      | [.agents/skills/superpowers/SKILL.md](.agents/skills/superpowers/SKILL.md)                                               | Quy trình 5 bước kỹ thuật: Spec & Brainstorm $\rightarrow$ Plan $\rightarrow$ TDD Execution $\rightarrow$ Systematic Debug $\rightarrow$ Review & Verify.                                           |
| **9**  | **TDD**                              | [.agents/skills/tdd/SKILL.md](.agents/skills/tdd/SKILL.md)                                                               | Chu trình Red-Green-Refactor: Viết test case kiểm thử logic đối soát dòng tiền, tính lệch tồn kho, idempotency, exception lifecycle trước khi code service/repository.                               |
| **10** | **Git Conventions**                  | [.agents/skills/git-conventions/SKILL.md](.agents/skills/git-conventions/SKILL.md)                                       | Chuẩn Conventional Commits (`feat(integrations): ...`, `fix(reconciliation): ...`), quy trình branch/PR gọn gàng theo từng chặng, Semantic Versioning.                                            |
| **11** | **UI/UX Pro Max**                    | [.agents/skills/ui-ux-pro-max/SKILL.md](.agents/skills/ui-ux-pro-max/SKILL.md)                                           | Thiết kế giao diện Dashboard vận hành đẳng cấp, triệt tiêu hoàn toàn "AI-slop", phân cấp thông tin rõ ràng cho Operations Cockpit (trạng thái sync, lệch đối soát, hàng chờ ngoại lệ).              |
| **12** | **Web Quality**                      | [.agents/skills/web-quality/SKILL.md](.agents/skills/web-quality/SKILL.md)                                               | Đảm bảo Core Web Vitals, HTML5 ngữ nghĩa, WCAG 2.1 AA accessibility, an toàn frontend (XSS/CSRF) và tối ưu rendering TanStack Query.                                                                 |
| **13** | **Caveman**                          | [.agents/skills/caveman/SKILL.md](.agents/skills/caveman/SKILL.md)                                                       | Giao tiếp cô đọng, tối đa mật độ thông tin, loại bỏ văn mẫu rườm rà. Dùng cho Hệ thống 1 (Fast Mode).                                                                                                |
| **14** | **Humanizer**                        | [.agents/skills/humanizer/SKILL.md](.agents/skills/humanizer/SKILL.md)                                                   | Viết tài liệu kỹ thuật, hướng dẫn vận hành, migration doc và commit message tự nhiên, mạch lạc, chính xác.                                                                                         |
| **15** | **Excalidraw**                       | [.agents/skills/excalidraw/SKILL.md](.agents/skills/excalidraw/SKILL.md)                                                 | Trực quan hóa kiến trúc luồng dữ liệu (Mermaid / Draw.io) cho quy trình Ingest $\rightarrow$ Normalize $\rightarrow$ Reconcile $\rightarrow$ Exception.                                             |
| **16** | **Find Skills**                      | [.agents/skills/find-skills/SKILL.md](.agents/skills/find-skills/SKILL.md)                                               | Tự động phát hiện và đề xuất bổ sung kỹ năng chuyên sâu phù hợp cho từng bài toán kỹ thuật mới (ví dụ xử lý file Excel/CSV, SDK sàn TMĐT).                                                         |
| **17** | **Deploy to Vercel**                 | [.agents/skills/deploy-to-vercel/SKILL.md](.agents/skills/deploy-to-vercel/SKILL.md)                                     | Cấu hình và triển khai ứng dụng frontend SPA lên hạ tầng cloud khi cần thiết.                                                                                                                        |
| **18** | **Remotion**                         | [.agents/skills/remotion/SKILL.md](.agents/skills/remotion/SKILL.md)                                                     | Tạo animation, motion graphics trực quan hóa quy trình đối soát phức tạp hoặc video demo tính năng nền tảng.                                                                                        |
| **19** | **evondevKit**                       | [.agents/skills/evondevKit/SKILL.md](.agents/skills/evondevKit/SKILL.md)                                                 | **(Chuẩn UI/UX Senior Evondev)**: Đánh giá và tối ưu giao diện bảng đối soát, modal giải quyết ngoại lệ, thanh lọc trạng thái kết nối, nhịp điệu typography và micro-interactions mượt mà.         |

---

## 3. CỔNG ĐIỀU PHỐI NHẬN THỨC: TƯ DUY NHANH & CHẬM (SYSTEM 1 VS SYSTEM 2)

Mọi input từ User trước hết được đánh giá bởi [Fast and Slow Thinking](.agents/skills/fast-and-slow-thinking/SKILL.md) để phân loại nhánh xử lý:

### Nhánh 1: Hệ Thống 1 (Tư Duy Nhanh - Fast Mode)

- **Đối tượng áp dụng**:
  - Chạy lệnh test/lint/typecheck (`pytest`, `ruff`, `mypy`, `pnpm test`, `make check`).
  - Kiểm tra log container, service status, alembic migration status.
  - Sửa lỗi cú pháp nhỏ, typo, import thiếu, formatting.
  - Git commit, push, tạo branch đơn giản.
- **Quy tắc thực thi**:
  - Không hỏi vòng vo, không kích hoạt quy trình phỏng vấn rườm rà.
  - Thực thi ngay lập tức, báo cáo súc tích bằng `Caveman`, tiết kiệm tối đa token (< 200 tokens).

### Nhánh 2: Hệ Thống 2 (Tư Duy Chậm - Slow Mode)

- **Đối tượng áp dụng**:
  - Thiết kế module mới (`integrations`, `exceptions`, `rules`).
  - Thiết kế hoặc thay đổi schema cơ sở dữ liệu PostgreSQL (Alembic migrations).
  - Tái cấu trúc logic nghiệp vụ cốt lõi (tách trừ kho vật lý ra khỏi import đơn, xây dựng công thức đối soát dòng tiền Settlement).
  - Tích hợp với webhook/API đối tác ngoài (Shopee, TikTok, Odoo ERP).
  - Debug sự cố sai lệch số liệu tài chính hoặc deadlock giao dịch.
- **Quy tắc thực thi (Bắt buộc qua sàng lọc chuyên sâu)**:
  1. _Tầng 1 (Brainstorming)_: So sánh phương án A vs Phương án B kèm Trade-offs và rủi ro trước khi viết code.
  2. _Tầng 2 (Grill-Me)_: Đặt 1-2 câu hỏi trắc nghiệm có cấu trúc (gợi ý A/B/C) để bóc tách edge cases, chốt Data Contract rõ ràng.
  3. _TDD Execution_: Viết test case kiểm thử trước khi code model/service.
  4. _ADR Record_: Ghi lại quyết định kiến trúc quan trọng vào thư mục `docs/adr/`.

---

## 4. CƠ CHẾ PHÂN TÍCH Ý ĐỒ & KÍCH HOẠT SKILL TỰ ĐỘNG (SKILL-AWARE ACTIVATION)

Khi nhận bất kỳ input nào từ User, AI Agent **bắt buộc phải thực hiện 3 bước**:

1. **Phân tích Yêu cầu (Intent Analysis)**:
   - _Yêu cầu mới, làm rõ nghiệp vụ đối soát, kết nối sàn, luồng xử lý ngoại lệ_ $\rightarrow$ Gọi `Brainstorming` + `Matt Pocock (Grill-me)`.
   - _Lỗi runtime, sai lệch số liệu đối soát, race condition_ $\rightarrow$ Gọi `Systematic Debugging & RCA` (tái hiện lỗi độc lập, 5 Whys).
   - _Thiết kế schema bảng snapshots, migration, partial index, khóa dòng_ $\rightarrow$ Gọi `Database Design & Optimization`.
   - _API contracts, DTO mappers, webhook signature, retry backoff_ $\rightarrow$ Gọi `API Design & Contracts`.
   - _Tái cấu trúc module, bảo vệ ranh giới modular monolith, viết ADR_ $\rightarrow$ Gọi `Clean Architecture & Refactoring`.
   - _Thiết kế giao diện bảng điều khiển vận hành, hàng chờ ngoại lệ, chi tiết đối soát_ $\rightarrow$ Gọi `evondevKit` + `UI/UX Pro Max` + `Impeccable` + `Web Quality`.
   - _Viết service logic, nghiệp vụ xử lý dữ liệu_ $\rightarrow$ Gọi `Superpowers` + `TDD`.
   - _Git branch, conventional commit, release versioning_ $\rightarrow$ Gọi `Git Conventions`.
   - _Chạy lệnh kiểm tra, xem log, tóm tắt nhanh_ $\rightarrow$ Gọi `Caveman`.
   - _Viết báo cáo kiểm toán, tài liệu kỹ thuật, hướng dẫn vận hành_ $\rightarrow$ Gọi `Humanizer`.
   - _Bàn giao chặng / kết thúc phase_ $\rightarrow$ Gọi `Matt Pocock (Handoff)`.
2. **Khai báo Chế độ & Kỹ năng Được Kích hoạt**:
   - Ví dụ: `[Chế độ: Tư Duy Nhanh (System 1) | Kỹ năng: Caveman]` HOẶC
   - Ví dụ: `[Chế độ: Tư Duy Chậm (System 2) | Kỹ năng: Clean Architecture & Refactoring + Database Design & Optimization + TDD]`
3. **Thực thi Chuẩn Mực**: Tuân thủ tuyệt đối các nguyên tắc kỹ thuật trong file `SKILL.md` của kỹ năng đó để đưa ra output tối ưu nhất, không có mã thừa, không văn mẫu sáo rỗng.
