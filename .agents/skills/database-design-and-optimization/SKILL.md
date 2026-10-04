---
name: database-design-and-optimization
description: |
    Enterprise database design, data modeling, concurrency control, and query optimization.
    Covers relational schema design, indexing strategies (B-Tree, composite, partial), row-level locking
    (SELECT FOR UPDATE, deadlock prevention), N+1 query elimination, and zero-downtime migrations.

    Relevant when:
      - Designing database schemas, tables, relationships, and constraints in PostgreSQL / Odoo.
      - Diagnosing slow queries, database locks, deadlocks, or transaction rollbacks.
      - Optimizing ORM performance (prefetching, batching, avoiding N+1 loops).
      - Planning non-blocking database migrations for production data safety.
---

# Database Design, Modeling & Query Optimization

Trong các hệ thống ERP bán lẻ và Backend xử lý giao dịch tài chính, **80% sự cố hệ thống bắt nguồn từ tầng Database**. Kỹ năng này cung cấp các nguyên tắc bất biến để thiết kế và tối ưu cơ sở dữ liệu chuẩn Senior Data/Backend Engineer.

---

## 1. Nguyên Tắc Thiết Kế Schema & Ràng Buộc Dữ Liệu (Constraints)

1. **Ràng buộc ở Database là Chân lý Cuối cùng (Database-level Constraints)**:
    - Không chỉ validate ở tầng code (Pydantic / Odoo python `@api.constrains`).
    - Bắt buộc phải có `UNIQUE constraint` (ví dụ: `UNIQUE(order_ref)`, `UNIQUE(transaction_no)`) để triệt tiêu 100% rủi ro tạo đơn/thanh toán trùng lặp khi có race conditions.
    - Luôn sử dụng `CHECK constraint` cho các giá trị nhạy cảm: `quantity >= 0`, `price_unit >= 0`.
    - Thiết lập `FOREIGN KEY` với `ON DELETE RESTRICT` cho dữ liệu kế toán và kho để chống việc xóa nhầm làm mất dữ liệu đối soát.

---

## 2. Chiến Lược Đánh Chỉ Mục (Indexing Strategy)

Chỉ mục (Index) giúp tăng tốc độ đọc (SELECT) nhưng làm chậm tốc độ ghi (INSERT/UPDATE). Senior SE chỉ đánh index có chủ đích:

### Các loại Index cần nắm vững:

1. **Foreign Key Indexing**: Luôn đánh B-Tree index trên các cột khóa ngoại (`partner_id`, `warehouse_id`, `order_id`).
2. **Composite Index (Chỉ mục kết hợp)**: Khi câu query thường xuyên lọc theo nhiều cột:
    ```sql
    CREATE INDEX idx_quant_product_location ON stock_quant (product_id, location_id);
    ```
    _Quy tắc Left-to-Right_: Cột có độ chọn lọc cao nhất (high cardinality) đặt bên trái.
3. **Partial Index (Chỉ mục có điều kiện)**: Tiết kiệm RAM và ổ đĩa cực lớn cho bảng nhiều triệu dòng:
    ```sql
    -- Chỉ đánh index cho các đơn hàng đang trong trạng thái khóa giữ tồn kho (chưa hoàn tất)
    CREATE INDEX idx_orders_holding ON sale_order (hold_expires_at)
    WHERE state = 'draft' AND hold_expires_at IS NOT NULL;
    ```

---

## 3. Quản Lý Độc Quyền & Khóa Dòng (Concurrency & Row Locking)

Khi hàng trăm khách cùng bấm mua 1 sản phẩm cuối cùng (Flash sale / Quét QR cùng lúc):

### Sai lầm chết người (Junior - Read-Modify-Write không khóa):

```python
# CODE NGUY HIỂM: Bị Race condition dẫn đến OVERSELL
quant = env['stock.quant'].search([('product_id', '=', pid), ('location_id', '=', loc_id)])
if quant.quantity >= requested_qty:
    quant.quantity -= requested_qty  # 2 request cùng đọc thấy còn hàng và cùng trừ!
```

### Chuẩn Senior (Pessimistic Row-level Locking):

```python
# CODE CHUẨN SENIOR: Khóa dòng ngay khi đọc trong 1 Transaction
self.env.cr.execute("""
    SELECT id, quantity, reserved_quantity
    FROM stock_quant
    WHERE product_id = %s AND location_id = %s
    FOR UPDATE NOWAIT;  -- Hoặc FOR UPDATE
""", (product_id, location_id))
```

- **Quy tắc chống Deadlock**: Luôn sắp xếp thứ tự khóa tài nguyên theo ID tăng dần (`ORDER BY id ASC`).

---

## 4. Triệt Tiêu Lỗi N+1 Query Trên ORM

### Triệu chứng:

Lặp qua 100 đơn hàng, mỗi vòng lặp lại bắn 1 câu query lấy tên khách hàng -> Sinh ra 101 câu query xuống Postgres!

### Giải pháp:

- **Odoo ORM**: Luôn dùng Recordset batching, không duyệt từng record để đọc field liên kết:
    ```python
    # TỐT: Odoo tự động prefetch trong 1 câu SQL IN (...)
    partners = orders.mapped('partner_id')

    # XẤU: Ép query lặp từng dòng
    for order in orders:
        partner_name = order.partner_id.name
    ```
- **Kiểm tra hiệu năng SQL**: Dùng `EXPLAIN (ANALYZE, BUFFERS)` để soi:
    - Tránh `Seq Scan` (quét toàn bộ bảng) trên bảng lớn.
    - Hướng tới `Index Scan` hoặc `Index Only Scan`.

---

## 5. Quy Chuẩn Migration Không Downtime (Zero-Downtime Migration)

Khi thêm cột hoặc sửa bảng production:

1. **Không bao giờ chạy `ALTER TABLE ADD COLUMN ... DEFAULT 'abc'`** trên bảng lớn của Postgres cũ mà không kiểm tra lock table.
2. Thêm cột mới nullable trước → Viết code đọc cột mới nhưng fallback về cột cũ → Backfill dữ liệu ngầm theo batch nhỏ → Đổi code sang cột mới → Xóa cột cũ sau cùng (Expand-Contract Pattern).
