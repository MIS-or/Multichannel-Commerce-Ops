---
name: git-conventions
description: |
    Comprehensive Git workflow, branch naming conventions, Conventional Commits, Pull Request (PR) lifecycle,
    semantic versioning (SemVer), and Odoo naming standards.
    Enforces clean version control, linear git history, atomic commits, and team collaboration hygiene.

    Relevant when:
      - Creating, naming, or switching Git branches.
      - Drafting commit messages (Conventional Commits standard).
      - Opening, reviewing, formatting, or merging Pull Requests (PRs).
      - Bumping module versions according to Odoo SemVer standards (<odoo_ver>.<major>.<minor>.<patch>).
      - Establishing file, model, field, and symbol naming conventions.
---

# Git Workflow, Version Control & Naming Conventions

Tài liệu này xác lập quy chuẩn kỹ thuật bắt buộc về quản lý mã nguồn Git, quy tắc đặt tên nhánh, viết commit message, quy trình Pull Request (PR), quản lý phiên bản (SemVer) và chuẩn đặt tên trong hệ sinh thái Odoo 18.

---

## 1. Quy Tắc Đặt Tên Nhánh (Branch Naming Convention)

Mọi nhánh làm việc phải tuân theo cấu trúc:

```text
<type>/<scope>-<short-description>
```

### Các tiền tố (Prefix Types):

| Prefix      | Ý Nghĩa                                   | Ví Dụ                                                  |
| :---------- | :---------------------------------------- | :----------------------------------------------------- |
| `feat/`     | Phát triển tính năng hoặc module mới      | `feat/inv-safety-buffer`, `feat/vnpay-provider`        |
| `fix/`      | Sửa lỗi (bug fix)                         | `fix/cron-stock-expiration`, `fix/vnpay-checksum`      |
| `refactor/` | Tái cấu trúc mã nguồn không đổi logic     | `refactor/theme-scss-tokens`, `refactor/quant-compute` |
| `docs/`     | Viết tài liệu, hướng dẫn, handoff         | `docs/reconciliation-guide`, `docs/setup-odoo18`       |
| `test/`     | Viết hoặc bổ sung test case TDD           | `test/stock-reservation-tdd`, `test/vnpay-ipn`         |
| `chore/`    | Cấu hình Docker, CI/CD, dọn dẹp phụ thuộc | `chore/docker-compose-cleanup`, `chore/odoo-conf`      |
| `release/`  | Chuẩn bị phát hành phiên bản mới          | `release/v18.0.1.0`                                    |

### Quy chuẩn bắt buộc:

- Toàn bộ dùng chữ thường (kebab-case), phân cách bằng dấu gạch ngang `-`.
- Không dùng tiếng Việt có dấu, không chứa khoảng trắng hay ký tự đặc biệt.
- Tên nhánh phải ngắn gọn nhưng nêu rõ đối tượng tác động (tối đa 40 ký tự).

---

## 2. Quy Chuẩn Commit Message (Conventional Commits)

Mỗi commit phải mang tính nguyên khối (atomic commit) - chỉ giải quyết một bài toán duy nhất.

### Cấu trúc chuẩn:

```text
<type>(<scope>): <subject>

[optional body: Giải thích TẠI SAO (WHY) thay đổi, không kể lể WHAT]

[optional footer: Closes #123, BREAKING CHANGE: ...]
```

### Types quy định:

- `feat`: Tính năng mới cho người dùng hoặc module mới.
- `fix`: Sửa lỗi phát sinh trong hệ thống.
- `refactor`: Tái cấu trúc code (không thêm feature, không fix bug).
- `style`: Thay đổi định dạng, khoảng trắng, SCSS/CSS không ảnh hưởng logic.
- `test`: Thêm hoặc chỉnh sửa unit test.
- `docs`: Chỉnh sửa tài liệu markdown, README, docstrings.
- `chore`: Thay đổi file build, docker-compose, gitignore, dependencies.

### Scope quy định trong dự án:

- `inventory`: Module quản lý kho & tồn đệm.
- `payment`: Module cổng thanh toán VNPay/VietQR.
- `theme`: Module theme & giao diện bán lẻ.
- `docker`: Cấu hình container, docker-compose.
- `rules`: Cập nhật AGENTS.md, guidelines.

### Quy tắc viết Subject:

- Dùng thể mệnh lệnh (Imperative mood): _"add"_, _"fix"_, _"implement"_, thay vì _"added"_, _"fixes"_.
- Không viết hoa chữ cái đầu tiên của subject.
- Không để dấu chấm `.` ở cuối dòng subject.
- Độ dài dòng subject không quá 72 ký tự.

### Ví dụ chuẩn:

```text
feat(inventory): add safety buffer field to stock.quant
fix(payment): resolve HMAC-SHA512 checksum mismatch on IPN webhook
refactor(theme): convert inline styles to SCSS design tokens
test(inventory): add test case for 15-minute stock hold expiration
chore(docker): configure odoo18 multi-workers in odoo.conf
```

---

## 3. Quy Trình Pull Request (PR) & Chiến Lược Merge

### Bước 1: Khởi tạo Pull Request

- **Tiêu đề PR**: Tuân theo đúng chuẩn Conventional Commits (ví dụ: `feat(inventory): implement multi-warehouse safety buffer`).
- **Nội dung PR**: Phải điền đầy đủ theo Template:
    ```markdown
    ## 1. Mục Tiêu (Objective)

    Mô tả bài toán nghiệp vụ cần giải quyết và lý do thay đổi.

    ## 2. Thay Đổi Chính (Key Changes)

    - Thêm model/field: ...
    - Cập nhật view/controller: ...

    ## 3. Kế Hoạch & Bằng Chứng Kiểm Thử (Test Plan & Verification)

    - [x] Python syntax check: Pass
    - [x] Odoo module install / upgrade: Pass
    - [x] Unit test: X/X passed

    ## 4. Tác Động Dữ Liệu (Breaking Changes / Migrations)

    Có thay đổi bảng database cũ không? Cần upgrade module `-u` không?
    ```

### Bước 2: Review & Tiêu Chuẩn Phê Duyệt (Review Checklist)

- Không có code thừa, không có print/console debug rác.
- Đã kiểm tra cú pháp không lỗi (`python -m py_compile`).
- Tuân thủ Odoo Guidelines và PEP 8.
- Không để lộ secret key, API key trong mã nguồn.

### Bước 3: Chiến Lược Merge (Merge Strategy)

- **Squash and Merge (Ưu tiên số 1)**: Toàn bộ các commit nhỏ trong nhánh tính năng sẽ được gộp thành 1 commit duy nhất trên nhánh `main`. Giúp lịch sử Git của nhánh chính luôn thẳng, sạch, dễ theo dõi và an toàn khi cần `git revert`.
- **Xóa nhánh (Delete branch)**: Luôn xóa feature branch sau khi merge thành công.

---

## 4. Quy Chuẩn Đặt Tên Trong Odoo (Odoo Naming Standards)

| Thành Phần                       | Quy Tắc Đặt Tên                           | Ví Dụ Chuẩn                                           |
| :------------------------------- | :---------------------------------------- | :---------------------------------------------------- |
| **Thư mục Module**               | `snake_case`, bắt đầu bằng tiền tố domain | `retail_inventory`, `payment_vnpay`                   |
| **Model Odoo**                   | Phân cấp bằng dấu chấm `.`, danh từ số ít | `retail.warehouse.buffer`, `payment.provider`         |
| **Field Many2one**               | Tận cùng bằng `_id`                       | `warehouse_id`, `partner_id`                          |
| **Field One2many / Many2many**   | Tận cùng bằng `_ids`                      | `line_ids`, `product_ids`                             |
| **Field Boolean**                | Bắt đầu bằng `is_`, `has_`, `can_`        | `is_central_dc`, `has_buffer`                         |
| **Phương thức Button/Action**    | Bắt đầu bằng `action_`                    | `action_confirm_hold()`, `action_release_stock()`     |
| **Phương thức Compute**          | Bắt đầu bằng `_compute_`                  | `_compute_available_qty()`                            |
| **Phương thức Onchange**         | Bắt đầu bằng `_onchange_`                 | `_onchange_warehouse_id()`                            |
| **Phương thức Nội bộ (Private)** | Bắt đầu bằng dấu gạch dưới `_`            | `_calculate_checksum()`, `_verify_signature()`        |
| **XML ID**                       | `<model_name>_<view_type>`                | `retail_warehouse_view_form`, `product_template_tree` |

---

## 5. Quản Lý Phiên Bản & Semantic Versioning (SemVer Odoo)

Phiên bản của mọi module Odoo trong `__manifest__.py` phải tuân theo cấu trúc 5 chữ số:

```text
<Odoo_Major>.<Module_Major>.<Module_Minor>.<Patch>
Ví dụ: 18.0.1.0.0
```

- **`18.0`**: Phiên bản Odoo nền tảng (cố định).
- **`Module_Major`** (`18.0.X.0.0`): Thay đổi kiến trúc lớn, phá vỡ cấu trúc cũ (Breaking Changes), cần script migration dữ liệu.
- **`Module_Minor`** (`18.0.1.X.0`): Bổ sung tính năng mới, thêm bảng/trường mới tương thích ngược.
- **`Patch`** (`18.0.1.0.X`): Sửa lỗi logic, cập nhật giao diện, không làm thay đổi cấu trúc bảng database.
