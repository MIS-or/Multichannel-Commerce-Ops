---
name: clean-architecture-and-refactoring
description: |
    Clean Architecture, SOLID design principles, code smell eradication, and Architecture Decision Records (ADR).
    Enforces maintainable software boundaries, separation of concerns, pragmatic refactoring techniques,
    and documentation of architectural decisions to eliminate technical debt and AI-generated code bloat.

    Relevant when:
      - Structuring Odoo modules, backend domain models, service layers, and business logic.
      - Refactoring messy, monolithic, or repetitive code into clean, modular abstractions.
      - Detecting and eliminating code smells (God Classes, Long Methods, Feature Envy, Shotgun Surgery).
      - Drafting Architecture Decision Records (ADR) to record critical technical choices and trade-offs.
---

# Clean Architecture, Refactoring & Architecture Decision Records (ADR)

Mã nguồn sinh bởi AI hoặc lập trình viên thiếu kinh nghiệm rất dễ rơi vào bẫy "AI-Slop" và "Big Ball of Mud": các file dài hàng nghìn dòng, trộn lẫn giao diện, dữ liệu và nghiệp vụ. Kỹ năng này xác lập tiêu chuẩn Clean Architecture và quản trị nợ kỹ thuật (Technical Debt) chuẩn Senior Software Engineer.

---

## 1. 5 Nguyên Tắc SOLID Trong Hệ Thống Thực Tế

1. **Single Responsibility (SRP - Đơn Trách Nhiệm)**:
    - Mỗi class/module chỉ nên có một lý do duy nhất để thay đổi.
    - _Ví dụ Odoo_: Tách riêng logic tính toán tồn kho (`stock.quant` / service) ra khỏi logic sinh hóa đơn VAT (`account.move` / service), không nhồi tất cả vào `sale.order`.
2. **Open/Closed (OCP - Mở Rộng Nhưng Không Sửa Đổi)**:
    - Tận dụng cơ chế kế thừa `_inherit` của Odoo để mở rộng tính năng mới thay vì chọc thẳng vào sửa core module có sẵn.
3. **Liskov Substitution (LSP - Thay Thế An Toàn)**:
    - Khi kế thừa model hoặc class, method override phải giữ nguyên kiểu dữ liệu trả về và contract, không được làm hỏng luồng chạy của lớp cha.
4. **Interface Segregation (ISP - Tách Biệt Giao Diện)**:
    - Không ép client phải phụ thuộc vào những method mà họ không sử dụng.
5. **Dependency Inversion (DIP - Đảo Ngược Phụ Thuộc)**:
    - Các module cấp cao (Business Logic đơn hàng) không phụ thuộc trực tiếp vào chi tiết cấp thấp (API client cổng thanh toán cụ thể), mà phụ thuộc qua interface/abstract provider (`payment.provider`).

---

## 2. Nhận Diện & Xử Lý Code Smells Điển Hình

| Code Smell                | Dấu Hiệu Nhận Biết                                                         | Kỹ Thuật Refactoring Chuẩn Senior                                                                                     |
| :------------------------ | :------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------- |
| **God Class / Mega File** | 1 file/class dài hơn 500-1000 dòng, chứa hàng chục trách nhiệm             | **Extract Class / Module**: Tách thành các service nhỏ chuyên trách (ví dụ: `PricingService`, `StockHoldService`).    |
| **Long Method**           | Hàm dài > 50 dòng, có nhiều cấp `if-else` lồng nhau                        | **Extract Method**: Chia nhỏ hàm thành các bước con mang tên mô tả rõ ý đồ (`_validate_stock()`, `_reserve_quant()`). |
| **Primitive Obsession**   | Truyền 7-8 tham số rời rạc (`customer_name`, `phone`, `street`, `ward`...) | **Introduce Parameter Object / Dataclass / DTO**: Gom thành 1 object `CustomerAddressDTO`.                            |
| **Shotgun Surgery**       | Mỗi lần sửa 1 logic nhỏ phải mở và sửa 6-7 file khác nhau                  | Gom các logic phụ thuộc về cùng 1 domain module duy nhất.                                                             |
| **Magic Numbers/Strings** | Hardcode `if status == 1`, `tax = 0.08`, `timeout = 900`                   | Khai báo hằng số có tên (`VAT_RATE_RETAIL = 0.08`, `STOCK_HOLD_SECONDS = 900`).                                       |

---

## 3. Quy Chuẩn Tài Liệu Quyết Định Kiến Trúc (ADR - Architecture Decision Records)

Khi đưa ra quyết định kiến trúc quan trọng (ví dụ: _"Tại sao dùng Odoo Monolith thay vì Microservices?"_, _"Tại sao dùng Pessimistic Lock thay vì Optimistic Lock?"_), Senior SE bắt buộc viết 1 bản ghi ADR:

### Cấu trúc 1 file ADR chuẩn (`docs/adr/001-xxx.md`):

```markdown
# ADR 001: Khóa Giữ Tồn Kho Nguyên Khối Trong Odoo (Atomic Stock Reservation)

## Trạng Thái (Status)

Đã duyệt (Accepted) - 2026-09-30

## Bối Cảnh (Context)

Hệ thống bán lẻ đa kênh có rủi ro oversell khi khách mua online đang quét QR thì khách tại quầy POS mua mất sản phẩm cuối cùng.

## Quyết Định (Decision)

Sử dụng phương thức `order.action_confirm()` của Odoo ngay khi tạo đơn nháp trên Web để sinh `stock.move` khóa trường `reserved_quantity`, kết hợp cron hủy đơn tự động sau 15 phút.

## Các Phương Án Đã Cân Nhắc (Alternatives Considered)

- **Phương án A (Optimistic)**: Chỉ trừ kho khi nhận IPN thành công → _Bị loại vì rủi ro oversell cao_.
- **Phương án B (Redis Cache Lock)**: Dùng Redis giữ lock bên ngoài Odoo → _Bị loại vì phân mảnh dữ liệu, POS trong Odoo không thấy được lock của Redis_.

## Hệ Quả & Đánh Đổi (Consequences & Trade-offs)

- **Ưu điểm**: POS thấy tồn kho giảm ngay lập tức, triệt tiêu 100% rủi ro oversell.
- **Đánh đổi**: Cần cron job dọn dẹp đơn hết hạn mỗi 5 phút; tăng số lượng record trong bảng `stock_move`.
```

---

## 4. Nguyên Tắc Hướng Đạo Sinh (The Boy Scout Rule)

> _"Luôn để lại mã nguồn sạch sẽ hơn lúc bạn tìm thấy nó."_

Mỗi khi mở 1 file để sửa bug hoặc thêm tính năng:

1. Xóa bỏ ít nhất 1 đoạn code thừa hoặc biến không dùng (dead code).
2. Đặt lại tên biến cho rõ nghĩa hơn nếu tên cũ quá tắt (`d` -> `duration_seconds`).
3. Chuẩn hóa format indentation và loại bỏ trailing whitespace.
