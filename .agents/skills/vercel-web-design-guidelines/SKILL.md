---
name: vercel-web-design-guidelines
description: 'Kiểm tra khả năng sử dụng (usability), chất lượng triển khai kỹ thuật, hệ thống khoảng cách phân cấp (systematic spacing), và quy trình kiểm tra thị giác bằng ảnh chụp desktop/mobile để loại bỏ lỗi xuống dòng, chữ nhỏ, lệch cân đối.'
---

# Vercel Web Design Guidelines - Kiểm Tra Sử Dụng & Triển Khai

Kỹ năng chuyên sâu đảm trách **tiêu chuẩn chất lượng triển khai (implementation quality), khả năng sử dụng (usability), hệ thống khoảng cách logic (systematic spacing) và quy trình kiểm định thị giác đa màn hình bằng ảnh chụp (visual viewport audit)** theo phong cách kỹ thuật cao cấp của Vercel Design Engineering.

---

## 1. Hệ Thống Khoảng Cách Phân Cấp (Systematic Spacing)

Khoảng cách không đơn thuần là khoảng trống, mà là công cụ trực quan mạnh nhất để người dùng nhận biết **nhóm thông tin** và **mức độ ưu tiên (Gestalt Law of Proximity)** mà không cần đọc chữ.

### 1.1. Thang Đo Không Gian Chuẩn (Spatial Scale: Bội số 4px & 8px)

Luôn bám sát hệ thống bước nhảy có quy luật, tuyệt đối không dùng margin/padding ngẫu nhiên:

| Token              | Kích Thước  | Ứng Dụng Thực Tế                                                                |
| :----------------- | :---------- | :------------------------------------------------------------------------------ |
| `gap-1` / `p-1`    | 4px         | Khoảng cách giữa icon và chữ nhỏ, khoảng cách nhãn phụ.                         |
| `gap-2` / `p-2`    | 8px         | Khoảng cách giữa nhãn (label) và ô nhập liệu (input); icon và tiêu đề phụ.      |
| `gap-3` / `p-3`    | 12px        | Khoảng cách giữa tiêu đề và đoạn mô tả ngắn bên dưới; padding nút nhỏ.          |
| `gap-4` / `p-4`    | 16px        | Padding tiêu chuẩn trong card; khoảng cách giữa các phần tử form thông thường.  |
| `gap-6` / `p-6`    | 24px        | Padding cho card lớn, bảng dữ liệu; khoảng cách giữa các khối sản phẩm kề nhau. |
| `gap-8` / `p-8`    | 32px        | Khoảng cách giữa các cột trong lưới sản phẩm; phân tách giữa các cụm tính năng. |
| `gap-12` / `py-12` | 48px        | Khoảng đệm section trên màn hình di động (mobile section spacing).              |
| `py-16` - `py-24`  | 64px - 96px | Khoảng đệm section trên màn hình máy tính để bàn (desktop section spacing).     |

### 1.2. Quy Tắc Khoảng Cách Trong Phải Nhỏ Hơn Ngoài (Padding < Margin)

- **Nguyên lý**: Khoảng cách bên trong một nhóm (inner padding/gap) **bắt buộc phải nhỏ hơn** khoảng cách giữa nhóm đó với các nhóm khác (outer margin/gap).
- **Ví dụ**:
    - Khoảng cách giữa ảnh sản phẩm và tên sản phẩm trong card: `12px` (`mb-3`).
    - Khoảng cách từ card này sang card kế tiếp: `24px` (`gap-6`).
    - Khoảng cách từ cả lưới sản phẩm tới tiêu đề section: `48px` (`mt-12`).
    - _Nếu làm ngược lại (khoảng cách bên trong lớn hơn khoảng cách bên ngoài), các phần tử sẽ trông như bị vỡ cụm và mất liên kết._

---

## 2. Tiêu Chuẩn Trải Nghiệm & Tương Tác Xúc Giác (Tactile Quality)

Giao diện cao cấp phải có phản hồi tức thì (instant feedback) và cảm giác chạm/bấm chân thực:

### 2.1. Đầy Đủ 4 Trạng Thái Cho Mọi Phần Tử Có Thể Bấm Được

Mọi nút bấm (button), thẻ liên kết (card link), ô chọn (checkbox/radio) đều phải có:

1. **Default**: Rõ ràng, dễ nhận biết là có thể tương tác.
2. **Hover**: Đổi sắc độ màu nhẹ hoặc nâng nhẹ bề mặt (`transition-all duration-150 ease-out hover:bg-primary-hover`).
3. **Active (Pressed)**: Co nhẹ lại khi nhấn chuột hoặc chạm ngón tay (`active:scale-[0.98] active:brightness-95`).
4. **Focus-Visible**: Viền tiêu điểm sáng rõ nét khi điều hướng bằng bàn phím:
    ```html
    class="focus-visible:outline-none focus-visible:ring-2
    focus-visible:ring-primary focus-visible:ring-offset-2"
    ```
    _Tuyệt đối không dùng `outline: none` mà không có `ring` thay thế!_
5. **Disabled**: Giảm độ đậm (`opacity-50 cursor-not-allowed`), có thông báo lý do nếu cần.

### 2.2. Vùng Chạm Di Động (Touch Targets ≥ 44×44px)

- Mọi nút bấm, icon menu, icon đóng modal, mũi tên carousel trên màn hình cảm ứng phải có diện tích chạm tối thiểu **44px × 44px**.
- Nếu icon chỉ có kích thước 20px, sử dụng `p-3` hoặc đặt bên trong wrapper container `min-h-[44px] min-w-[44px] flex items-center justify-center`.

### 2.3. Triệt Tiêu Dịch Chuyển Bố Cục (Cumulative Layout Shift - CLS = 0)

- Mọi thẻ hình ảnh `<img>` bắt buộc phải có thuộc tính `width`, `height` hoặc class tỷ lệ cố định (`aspect-square`, `aspect-[4/3]`, `aspect-[16/9]`).
- Trước khi dữ liệu tải xong: Sử dụng khung xương tải trang (Skeleton loader) có kích thước trùng khớp 100% với component thật, ngăn chặn hiện tượng màn hình nhảy giật khi ảnh hoặc dữ liệu xuất hiện.

---

## 3. Quy Trình Kiểm Tra Bằng Ảnh Chụp (Dual-Viewport Audit Protocol)

Không bao giờ coi một tính năng UI là hoàn thiện nếu chưa kiểm tra bằng mắt thực tế qua ảnh chụp ở cả 2 độ phân giải: **Desktop (1440px / 1280px)** và **Mobile (375px / 390px)**.

### 3.1. Các Bước Tiến Hành Kiểm Định Thị Giác

1. Khởi chạy giao diện và chụp ảnh toàn bộ trang (Full-page screenshot) ở kích thước Desktop và Mobile.
2. Rà soát tuần tự 5 điểm nghẽn thị giác dưới đây:

### 3.2. Năm Lỗi Cần Sửa Ngay Lập Tức Khi Xem Ảnh Chụp

#### ① Lỗi Xuống Dòng Vụn Vặt (Awkward Wrapping & Broken Buttons)

- **Hiện tượng**: Tiêu đề bị rớt 1 từ cụt ngủn xuống hàng mới; nút bấm bị ép chữ thành 2 hàng méo mó (ví dụ: _"Xem chi"_ dòng trên, _"tiết"_ dòng dưới).
- **Cách sửa**:
    - Dùng `[text-wrap:balance]` cho tiêu đề.
    - Thêm `whitespace-nowrap` cho các nút bấm hành động ngắn.
    - Bổ sung `&nbsp;` nối các cụm từ ngắn đi kèm.

#### ② Lỗi Chữ Quá Nhỏ Trên Mobile (Micro-Text Issues)

- **Hiện tượng**: Chữ chú thích hoặc bảng thông số kỹ thuật bị co nhỏ dưới 13px trên điện thoại, khiến người dùng phải zoom bằng tay.
- **Cách sửa**:
    - Đảm bảo font size body trên mobile tối thiểu 15px - 16px.
    - Ô nhập dữ liệu (`<input>`, `<select>`) trên mobile bắt buộc từ 16px trở lên để ngăn trình duyệt iOS Safari tự động phóng to màn hình khi gõ.

#### ③ Lỗi Khoảng Trống Thừa/Thiếu & Thiếu Cân Đối (Asymmetric Gaps)

- **Hiện tượng**:
    - Padding lề trái lề phải của mobile bị dính sát viền màn hình (dưới 16px).
    - Khoảng trống giữa 2 section quá mênh mông như bị đứt quãng trang web.
    - Các card trong cùng một hàng có chiều cao so le thụt thò (card có 2 dòng chữ cao hơn card có 1 dòng chữ).
- **Cách sửa**:
    - Đồng bộ padding ngang mobile: Luôn giữ `px-4 sm:px-6 lg:px-8`.
    - Cố định chiều cao card bằng flexbox: `flex flex-col justify-between h-full`.

#### ④ Lỗi Bảng Dữ Liệu & Bảng Thông Số Bị Ép Tràn (Table Squishing)

- **Hiện tượng**: Bảng thông số kỹ thuật nhiều cột khi sang mobile bị bóp méo, chữ dính vào nhau không đọc được.
- **Cách sửa**:
    - Cho phép bảng cuộn ngang mượt mà: Bọc bảng trong `<div class="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0">`.
    - Hoặc chuyển đổi cấu trúc bảng sang dạng danh sách thẻ (Stacked Cards / Key-Value List) trên màn hình nhỏ (`md:hidden`).

#### ⑤ Lỗi Thanh Cuộn Ngang Ngoài Ý Muốn (Unintended Horizontal Scroll)

- **Hiện tượng**: Trên mobile có thể gạt màn hình sang ngang, lộ ra khoảng trắng bên phải.
- **Cách sửa**:
    - Tìm phần tử có độ rộng cố định (`w-[500px]`, `w-screen` kết hợp padding, hoặc ảnh thiếu `max-w-full`).
    - Sửa phần tử con vượt giới hạn thay vì chỉ ẩn giấu bề mặt bằng `overflow-x: hidden` trên `<body>`.

---

## 4. Bảng Kiểm Tra Triển Khai (Vercel Implementation Checklist)

Trước khi bàn giao bất kỳ giao diện nào:

- [ ] **Khoảng cách có quy luật**: Toàn bộ padding/margin tuân thủ thang 4px/8px? Khoảng cách trong nhỏ hơn khoảng cách ngoài?
- [ ] **Đầy đủ trạng thái tương tác**: Mọi nút bấm, link có hover, active (`scale-[0.98]`), focus-visible ring rõ ràng?
- [ ] **Touch target thân thiện**: Không có nút nào nhỏ hơn 44×44px trên mobile?
- [ ] **Đã duyệt ảnh chụp Desktop (1440px)**: Tiêu đề cân đối, bố cục rộng rãi, không bị kéo dãn dòng chữ quá dài?
- [ ] **Đã duyệt ảnh chụp Mobile (375px/390px)**: Không cuộn ngang, không vỡ nút bấm, chữ không nhỏ hơn 14px, không có từ mồ côi?
- [ ] **Không dịch chuyển giao diện (CLS = 0)**: Ảnh có aspect-ratio hoặc kích thước xác định?
