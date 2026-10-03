---
name: impeccable
description: 'Phụ trách định hướng và tinh chỉnh giao diện, loại bỏ hoàn toàn "AI slop", thiết kế bố cục theo nội dung (sản phẩm, thông số kỹ thuật, câu chuyện thương hiệu), sử dụng hình ảnh và nội dung thực tế, nâng tầm thẩm mỹ và tính hoàn thiện cao cấp cho website.'
---

# Impeccable - Định Hướng & Tinh Chỉnh Giao Diện

Kỹ năng chuyên sâu đảm trách **định hướng thẩm mỹ, tính nguyên bản và độ hoàn thiện (craftsmanship)** của giao diện người dùng. Mục tiêu cốt lõi: triệt tiêu hoàn toàn hiện tượng **"AI Slop"** (giao diện đại trà, nhạt nhẽo, hiệu ứng rập khuôn do AI sinh ra), thay thế bằng thiết kế có chủ đích, phản ánh chính xác bản sắc thương hiệu và đặc thù ngành hàng.

---

## 1. Tuyên Ngôn Triệt Tiêu "AI Slop" (Anti-AI Slop Manifesto)

### Nhận diện "AI Slop" trong UI:

1. **Card Soup vô hồn**: Mọi nhóm thông tin đều bị nhét vào các thẻ bo tròn giống hệt nhau (`rounded-xl p-6 shadow-sm border`), bất kể là số liệu, hình ảnh, văn bản hay tính năng.
2. **Hiệu ứng trang trí vô nghĩa**: Lạm dụng gradient tím/xanh ngẫu nhiên, vệt sáng làm mờ (glowing blur blobs), hiệu ứng kính mờ (glassmorphism) không ăn nhập với thương hiệu.
3. **Nội dung sáo rỗng & số liệu giả**: Các câu khẩu hiệu rập khuôn như _"Giải pháp hàng đầu thế giới"_, _"Đổi mới công nghệ tương lai"_, kèm theo các số liệu vô căn cứ (_"99.9% Hài lòng"_).
4. **Bố cục đồng dạng**: Trang nào cũng có Hero section chữ to ở giữa -> 3 cards tính năng -> 1 banner CTA -> Footer. Không có nhịp điệu thị giác (visual rhythm).

### Nguyên tắc "Impeccable" thay thế:

- **Từng pixel đều có lý do tồn tại (Intentionality)**: Mọi khoảng cách, viền (border), độ đậm chữ và màu sắc đều phục vụ việc dẫn dắt sự chú ý của người dùng.
- **Bản sắc công nghiệp & thương mại đặc thù**: Với ngành sản xuất & phân phối nhựa (Nhựa Thuận Đạt), giao diện phải toát lên sự **bền vững, chuẩn xác, tin cậy công nghiệp (B2B)** kết hợp với **sự tiện lợi, thẩm mỹ tinh tế (B2C)**.
- **Dữ liệu thật, vật liệu thật**: Thay thế hình ảnh stock vô hồn bằng hình ảnh sản phẩm thực, quy trình ép phun, hạt nhựa nguyên sinh, tiêu chuẩn nhà máy và chứng nhận kỹ thuật.

---

## 2. Bố Cục Theo Nội Dung (Content-Driven Layout)

Không bao giờ ép các loại nội dung khác nhau vào cùng một khuôn mẫu (template). Mỗi dạng nội dung đòi hỏi một cấu trúc trình bày riêng biệt:

### 2.1. Danh Sách Sản Phẩm (Product Catalog & Commerce)

- **Mục tiêu**: Hỗ trợ quét nhanh (quick scanning), so sánh thông số và quyết định đặt hàng (bán lẻ & đặt hàng số lượng lớn B2B).
- **Cấu trúc tối ưu**:
    - Không chỉ có ảnh và giá: Hiển thị ngay thuộc tính kỹ thuật cốt lõi (chất liệu nhựa: `HDPE`, `PP`, `PET`; dung tích/kích thước; số lượng đóng gói tối thiểu `MOQ`).
    - Phân cấp thẻ sản phẩm:
        - **Ảnh sản phẩm**: Tỷ lệ chuẩn (1:1 hoặc 4:3), nền sạch hoặc hiệu ứng tương phản nhẹ với màu nền thương hiệu.
        - **Huy hiệu trạng thái (Status Badges)**: _Sẵn hàng trong kho_, _Sản xuất theo đơn_, _Hạt nhựa nguyên sinh_, _Chuẩn FDA_.
        - **Giá & Tùy chọn đặt hàng**: Phân biệt rõ giá niêm yết, khoảng giá sỉ theo số lượng (Tiered pricing), nút yêu cầu báo giá/thêm giỏ hàng rõ ràng.
    - Hỗ trợ cả hai chế độ xem: **Lưới (Grid)** cho trải nghiệm thị giác và **Bảng (Table/List)** cho khách hàng B2B mua số lượng lớn theo bảng quy cách.

### 2.2. Thông Số Kỹ Thuật (Technical Specifications & Data Sheets)

- **Mục tiêu**: Minh bạch, chuẩn xác, tạo độ tin cậy tuyệt đối cho kỹ sư, phòng mua hàng và đối tác B2B.
- **Cấu trúc tối ưu**:
    - **Bảng dữ liệu phân cấp (Structured Key-Value Tables)**:
        - Dùng xen kẽ hàng nền trắng / nền phụ nhẹ để tránh hoa mắt khi tra cứu.
        - Cột nhãn thuộc tính (30-40% chiều rộng, màu chữ thứ cấp, `font-medium`).
        - Cột giá trị (60-70% chiều rộng, chữ màu chính, số liệu dùng font đồng độ rộng / tabular figures).
    - **Dung sai & Tiêu chuẩn đo lường**: Luôn kèm đơn vị đo chuẩn (`mm`, `ml`, `gram`, `± 0.5%`).
    - **Khu vực tải tài liệu kỹ thuật**: Nút tải bảng vẽ kỹ thuật (Technical Drawing / 2D PDF), chứng nhận kiểm định chất lượng (Quatest, SGS, ISO, RoHs) có biểu tượng rõ ràng và dung lượng file.

### 2.3. Câu Chuyện Thương Hiệu & Năng Lực Sản Xuất (Brand Story & Factory Narrative)

- **Mục tiêu**: Xây dựng niềm tin sâu sắc, truyền tải quy mô nhà xưởng và tâm huyết người làm nghề.
- **Cấu trúc tối ưu**:
    - **Bố cục dạng tạp chí (Editorial Layout)**:
        - Phá vỡ lưới thẻ chữ nhật đều đặn: Kết hợp ảnh toàn cảnh nhà máy (full-bleed/wide banner), khối trích dẫn lớn từ nhà sáng lập (pull-quote), và các cột văn bản có độ rộng vừa phải (`max-w-prose`).
        - **Dòng thời gian phát triển (Milestone Timeline)**: Thiết kế tiến trình năm tháng có nhịp điệu, mỗi cột mốc gắn với một bước nhảy vọt về công nghệ khuôn mẫu hoặc năng lực nhà máy.
        - **Số liệu năng lực (Capacity Stats)**: Diện tích nhà xưởng, số lượng máy ép phun tự động, sản lượng hàng triệu sản phẩm/tháng — trình bày dạng cụm số lớn nổi bật (`text-4xl` hoặc `text-5xl`), bên dưới là chú thích ngắn gọn súc tích.

---

## 3. Hình Ảnh & Nội Dung Cụ Thể (Authenticity Over Generic Placeholders)

### 3.1. Nguyên Tắc Hình Ảnh Thực Tế

- **Ưu tiên số 1**: Dùng hình ảnh thực tế của nhà máy, dây chuyền thổi chai/ép phôi, hạt nhựa nguyên sinh và sản phẩm thật đã chụp.
- **Xử lý hình ảnh**:
    - Tách nền sạch sẽ, giữ đổ bóng tiếp xúc chân thực (contact shadow), không để sản phẩm lơ lửng vô lý trên nền trắng toát.
    - Đối với hình ảnh phối cảnh đời sống (lifestyle / ứng dụng thực tế): hiển thị sản phẩm được sử dụng đúng bối cảnh (ví dụ: chai nhựa mỹ phẩm trong phòng tắm sang trọng, can đựng hóa chất trong kho công nghiệp).
- **Tuyệt đối cấm**:
    - Ảnh minh họa 3D hoạt họa AI kỳ quặc, bàn tay 6 ngón hoặc máy móc cơ khí phi thực tế.
    - Ảnh stock phương Tây lạ lẫm không phù hợp với văn hóa và nhà xưởng thực tế tại Việt Nam.

### 3.2. Nội Dung Cụ Thể, Không Viết Sáo Rỗng

- **Kém (AI Slop)**: _"Chúng tôi cung cấp các giải pháp bao bì nhựa hàng đầu với chất lượng vượt trội và giá cả cạnh tranh nhất thị trường."_
- **Đạt chuẩn Impeccable**: _"Nhựa Thuận Đạt vận hành hệ thống máy ép phun tự động từ 120T đến 650T, chuyên gia công bao bì nhựa HDPE, PP, PET nguyên sinh 100%, đáp ứng dung sai chính xác dưới ±0.2mm và tiêu chuẩn an toàn tiếp xúc thực phẩm ISO 9001:2015."_

---

## 4. Tinh Chỉnh Bề Mặt & Chi Tiết (Surfaces, Borders & Depth)

Để giao diện không bị phẳng lì như một bản mockup dở dang hoặc quá lố bởi hiệu ứng AI:

1. **Hệ thống phân cấp bề mặt (Surface Hierarchy)**:
    - **Tầng nền (Canvas / Background)**: Thường là gam màu ấm hoặc trung tính tự nhiên (ví dụ `#F7F1E8` - màu cát/be ấm áp của Thuận Đạt).
    - **Tầng khối (Elevated Surface)**: Nền thẻ, bảng (`#FFFFFF` hoặc tông màu sáng hơn nền 1 bậc) để tạo sự nâng đỡ trực giác.
    - **Tầng nổi (Floating / Popover)**: Modal, Dropdown menu, Toast notification có bóng đổ mềm tự nhiên nhiều lớp (`box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05)`).
2. **Đường viền tinh tế (Subtle Borders)**:
    - Tránh viền đen thô hoặc viền xám đậm cứng nhắc.
    - Sử dụng viền có độ trong suốt hoặc màu pha với nền thương hiệu (ví dụ `border-brand-gold/40` hoặc viền tông đất ấm áp `border-[#D9C3A8]`).
3. **Căn chỉnh quang học (Optical Alignment)**:
    - Các icon, nút bấm hình tròn, mũi tên điều hướng phải được căn theo trọng tâm thị giác của mắt người (optical center), không phụ thuộc mù quáng vào căn giữa tuyệt đối toán học (mathematical center).

---

## 5. Quy Trình Rà Soát Impeccable (Review Checklist)

Trước khi nghiệm thu bất kỳ màn hình hoặc component mới nào:

- [ ] **Thoát khỏi Card Soup**: Có phần tử nào có thể hiển thị tự do, không cần đóng khung vào card không?
- [ ] **Khớp với dạng nội dung**: Danh sách sản phẩm, bảng thông số và câu chuyện thương hiệu đã dùng bố cục chuyên biệt chưa?
- [ ] **Hình ảnh chân thực**: Toàn bộ ảnh đã là sản phẩm/nhà xưởng thực tế, không có ảnh minh họa AI dị biệt?
- [ ] **Nội dung sắc bén**: Toàn bộ text đã mang thông tin cụ thể (chất liệu, kích thước, tiêu chuẩn), xóa sạch từ ngữ sáo rỗng?
- [ ] **Nhịp điệu thị giác cân đối**: Khoảng nghỉ giữa các section hợp lý, không gian thoáng đãng mà không bị trống trải?
