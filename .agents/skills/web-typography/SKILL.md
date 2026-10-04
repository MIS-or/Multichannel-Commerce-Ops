---
name: web-typography
description: 'Dùng khi cần xử lý sâu hệ thống chữ (typography). Thiết lập vai trò phân cấp chữ rõ ràng (tiêu đề, nội dung, chú thích, số liệu), tối ưu nhịp điệu đọc, loại bỏ từ mồ côi/rớt dòng, và kiểm tra hiển thị hoàn hảo dấu tiếng Việt không bị lỗi font fallback.'
---

# Web Typography - Hệ Thống Chữ Chuyên Sâu

Kỹ năng chuyên sâu đảm trách **hệ thống chữ, tính dễ đọc (readability), nhịp điệu dòng (vertical rhythm), căn lề số liệu và tối ưu hiển thị chữ tiếng Việt hoàn mỹ**. Chữ không chỉ là phương tiện truyền tải thông tin, mà là cốt lõi của giao diện người dùng.

---

## 1. Bốn Vai Trò Chữ Rõ Ràng (Typographic Hierarchy)

Mọi khối văn bản trên giao diện đều phải thuộc về một trong bốn vai trò được xác định rõ ràng, không sử dụng kích thước hoặc độ đậm (font-weight) tùy tiện:

| Vai Trò                             | Font & Cỡ Chữ                                     | Line-height                      | Letter-spacing                                          | Mục Đích & Trường Hợp Sử Dụng                                                                         |
| :---------------------------------- | :------------------------------------------------ | :------------------------------- | :------------------------------------------------------ | :---------------------------------------------------------------------------------------------------- |
| **Tiêu đề (Headings / Display)**    | `font-heading` (`Plus Jakarta Sans`), 20px - 48px | `leading-[1.1]` - `leading-snug` | `tracking-tight` (-0.02em)                              | Tiêu đề trang, tên sản phẩm, tiêu đề section. Cần dứt khoát, bắt mắt, ngắt dòng cân đối.              |
| **Nội dung (Body Text)**            | `font-sans` (`Inter`), 15px - 16px (1rem)         | `leading-relaxed` (1.5 - 1.625)  | `tracking-normal` (0)                                   | Đoạn mô tả sản phẩm, bài viết tin tức, giới thiệu thương hiệu. Tối ưu cho việc đọc lâu không mỏi mắt. |
| **Chú thích (Captions & Metadata)** | `font-sans`, 12px - 14px (0.75rem - 0.875rem)     | `leading-normal` (1.4)           | `tracking-normal` hoặc `tracking-wider` (nếu uppercase) | Mã SKU, ngày cập nhật, ghi chú dung sai, nhãn trạng thái (badge), breadcrumbs.                        |
| **Số liệu (Numbers & Metrics)**     | `font-mono` (`IBM Plex Mono`) hoặc `tabular-nums` | `leading-none` - `leading-tight` | `tracking-tight`                                        | Giá tiền, số lượng tồn kho, kích thước mm, trọng lượng g, tỷ lệ phần trăm %.                          |

---

## 2. Tiêu Chuẩn Chi Tiết Cho Từng Vai Trò

### 2.1. Tiêu Đề (Headings: H1, H2, H3)

- **Quy tắc độ chặt dòng (Tight Leading)**: Tiêu đề cỡ lớn bắt buộc phải có chiều cao dòng gọn gàng (`leading-tight` hoặc `leading-[1.15]`). Để `line-height: 1.5` trên tiêu đề cỡ lớn sẽ làm các dòng xa nhau rời rạc, làm vỡ khối thị giác.
- **Cân bằng ngắt dòng (Text Wrap Balance)**:
    - Luôn áp dụng thuộc tính `text-wrap: balance;` (hoặc class Tailwind `[text-wrap:balance]`) cho thẻ tiêu đề.
    - Ngăn chặn tuyệt đối hiện tượng **"từ mồ côi" (orphan/widow)** — khi một tiêu đề dài bị rớt đúng 1 từ duy nhất xuống dòng thứ hai.
- **Ví dụ chuẩn Tailwind**:
    ```html
    <h1
        class="font-heading text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-foreground leading-[1.15] [text-wrap:balance]"
    >
        Giải pháp bao bì nhựa chuẩn xác cho ngành công nghiệp & tiêu dùng
    </h1>
    ```

### 2.2. Nội Dung (Body Text)

- **Độ dài dòng tối ưu (Measure)**:
    - Mắt người đọc thoải mái nhất ở độ dài từ **45 đến 75 ký tự mỗi dòng** (tương đương `max-w-prose` hoặc `max-w-2xl` ~ 65ch).
    - **Lỗi nghiêm trọng cần tránh**: Để một đoạn văn mô tả tràn hết chiều rộng màn hình Desktop (1440px). Người dùng sẽ bị mất dấu dòng khi đọc từ cuối dòng này sang đầu dòng kế tiếp.
- **Kích thước tối thiểu trên Mobile**:
    - Không bao giờ đặt cỡ chữ nội dung dưới **15px** trên thiết bị di động (ưu tiên chuẩn 16px để chống giật zoom trên iOS Safari khi focus vào ô nhập liệu).
- **Ví dụ chuẩn Tailwind**:
    ```html
    <p
        class="font-sans text-base leading-relaxed text-foreground/80 max-w-prose [text-wrap:pretty]"
    >
        Được sản xuất trên dây chuyền ép phun áp lực cao, mỗi sản phẩm can nhựa
        5 lít của Thuận Đạt đảm bảo độ dày thành đồng đều và khả năng xếp chồng
        an toàn khi vận chuyển đường dài.
    </p>
    ```

### 2.3. Chú Thích & Nhãn (Captions, Labels & Metadata)

- Sử dụng màu sắc có độ tương phản thứ cấp dịu mắt (`text-muted-foreground` hoặc mã màu đất sẫm `#6B5B4E`).
- Với các nhãn trạng thái (Badge, Tag): Giới hạn kích thước từ 11px - 13px, có thể phối hợp `font-semibold uppercase tracking-wider` để tăng tính nhận diện mà không gây thô cứng.

### 2.4. Số Liệu, Giá Cả & Bảng Tính (Numbers & Tabular Data)

- **Số liệu đồng độ rộng (Tabular Figures)**:
    - Khi hiển thị giá tiền, số đo kỹ thuật trong bảng hoặc danh sách so sánh, kích hoạt CSS:
        ```css
        font-variant-numeric: tabular-nums;
        /* Hoặc class Tailwind: tabular-nums */
        ```
    - Đảm bảo các con số (0-9) có chiều rộng bằng nhau chính xác, giúp cột số tiền và số đo thẳng hàng dọc hoàn hảo, không bị thụt thò so le khi số thay đổi.
- **Ký hiệu tiền tệ và đơn vị đo**:
    - Luôn sử dụng khoảng trắng không ngắt dòng (`&nbsp;`) giữa số và đơn vị để tránh trường hợp số ở dòng trên, đơn vị rớt xuống dòng dưới:
        - Đúng: `250.000&nbsp;₫`, `500&nbsp;ml`, `2.5&nbsp;kg`, `±0.2&nbsp;mm`.
        - Sai: `250.000 ₫` (rất dễ rớt `₫` xuống dòng mới khi màn hình co hẹp).
- **Căn lề chuẩn cho bảng**:
    - Cột văn bản (tên hàng, mô tả): Căn trái (`text-left`).
    - Cột trạng thái, mã số ngắn: Căn giữa (`text-center`).
    - Cột số lượng, kích thước, đơn giá, thành tiền: **Bắt buộc căn phải (`text-right`)**.

---

## 3. Kiểm Tra Đầy Đủ Dấu Tiếng Việt (Vietnamese Diacritics Integrity)

Tiếng Việt có hệ thống nguyên âm phức tạp với các dấu phụ và dấu thanh ghép (ví dụ: `ệ`, `ở`, `ẵ`, `ộ`, `ự`, `đ`). Nếu không xử lý đúng, giao diện sẽ xuất hiện nhiều lỗi thẩm mỹ:

### 3.1. Chống Lỗi Font Fallback Glitching

- **Hiện tượng**: Một số font nước ngoài chỉ hỗ trợ ký tự Latinh cơ bản. Khi gặp chữ `ư`, `ơ`, `ễ`, trình duyệt phải lấy chữ từ font dự phòng (Arial, Times New Roman), tạo ra các ký tự bị lệch kích thước, nét thanh nét đậm không đều và nhảy chân dòng chữ (baseline jitter).
- **Giải pháp**:
    - Kiểm tra link nạp Google Fonts luôn khai báo bộ ký tự tiếng Việt:
        ```html
        <link
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap&subset=vietnamese"
            rel="stylesheet"
        />
        ```
    - Trong `tailwind.config.js`, luôn để hệ thống font dự phòng tương thích cao:
        ```js
        fontFamily: {
          sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
          heading: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
          mono: ['IBM Plex Mono', 'Menlo', 'monospace'],
        }
        ```

### 3.2. Cảnh Giác Với Chữ In Hoa (Uppercase) Tiếng Việt

- **Quy tắc**: Tuyệt đối không dùng `uppercase` cho cả một đoạn văn bản hoặc tiêu đề dài có nhiều dấu thanh ghép.
- **Lý do**: Khi viết hoa toàn bộ (`HƯỚNG DẪN ĐẶT HÀNG SẢN PHẨM KHUÔN ÉP PHUN ĐỘC QUYỀN`), các dấu thanh như dấu ngã (~), hỏi (?), nặng (.) đặt phía trên chữ hoa sẽ bị cấn vào dòng phía trên hoặc làm tiêu đề trông nặng nề, khó đọc.
- **Khuyến nghị**: Sử dụng **Title Case** (Viết Hoa Chữ Cái Đầu) hoặc **Sentence Case** (Chỉ viết hoa chữ đầu câu) cho tiêu đề tiếng Việt.

### 3.3. Giãn Chữ (Letter-spacing / Tracking) Trên Tiếng Việt

- Chỉ dùng `tracking-wider` hoặc `tracking-widest` cho các chuỗi ký tự viết hoa ngắn không dấu hoặc có dấu đơn giản (như mã sản phẩm `SKU-HDPE-01`, `MENU`, `HOTLINE`).
- **Không bao giờ** tăng tracking rộng trên văn bản tiếng Việt thường (`text-base tracking-widest`), vì khoảng cách giữa các chữ cái sẽ làm dấu thanh bị lệch trục quang học so với nguyên âm gốc.

---

## 4. Bảng Tra Cứu Thang Tỷ Lệ (Typographic Scale Reference)

Dành cho dự án Laravel / Tailwind CSS:

```css
/* Tỷ lệ chữ khuyến nghị */
.text-display {
    font-size: clamp(2.25rem, 5vw, 3.5rem); /* 36px -> 56px */
    line-height: 1.1;
    letter-spacing: -0.025em;
    font-weight: 800;
}

.text-h1 {
    font-size: clamp(1.875rem, 4vw, 2.5rem); /* 30px -> 40px */
    line-height: 1.2;
    letter-spacing: -0.02em;
    font-weight: 700;
}

.text-h2 {
    font-size: clamp(1.5rem, 3vw, 2rem); /* 24px -> 32px */
    line-height: 1.25;
    letter-spacing: -0.015em;
    font-weight: 700;
}

.text-h3 {
    font-size: 1.25rem; /* 20px */
    line-height: 1.4;
    font-weight: 600;
}

.text-body {
    font-size: 1rem; /* 16px */
    line-height: 1.625;
    font-weight: 400;
}

.text-caption {
    font-size: 0.8125rem; /* 13px */
    line-height: 1.4;
    font-weight: 500;
}
```

---

## 5. Danh Sách Kiểm Tra Hoàn Thiện (Typography Audit Checklist)

Mỗi khi chỉnh sửa văn bản, typography hoặc component:

- [ ] **Phân vai rõ ràng**: Có xác định được ngay đây là Tiêu đề, Nội dung, Chú thích hay Số liệu không?
- [ ] **Không bị lỗi font tiếng Việt**: Các chữ `ư`, `ơ`, `ễ`, `ậ`, `đ` có cùng độ dày và phong cách với chữ không dấu hay bị lệch font?
- [ ] **Không có từ rớt đơn độc (No Orphans/Widows)**: Tiêu đề có áp dụng `text-wrap: balance`? Không có chữ nào trơ trọi một mình một dòng?
- [ ] **Độ dài dòng hợp lý**: Đoạn văn bản dài có bị kéo dãn quá 75 ký tự/dòng không? (Đã gắn `max-w-prose` hoặc container thích hợp chưa?)
- [ ] **Số liệu thẳng hàng**: Cột giá tiền, bảng thông số có bật `tabular-nums` và căn phải `text-right` chưa?
- [ ] **Khoảng trắng đơn vị**: Các đơn vị (`₫`, `ml`, `kg`, `mm`) có nối bằng `&nbsp;` với con số phía trước không?
