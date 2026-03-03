# Tài liệu Đặc tả API QLDT

Tài liệu này cung cấp các thông số kỹ thuật cho các API đồng bộ hóa dữ liệu từ hệ thống QLDT vào phân hệ `ev_tnu_qldt_api` của Odoo.

## 1. Xác thực (Authentication)

Tất cả các API (ngoại trừ API đăng nhập) đều yêu cầu một mã xác thực Bearer Token trong tiêu đề (header) `Authorization`.

### API Đăng nhập
**URL:** `/api/v1/qldt/login`  
**Phương thức:** `POST`  
**Dữ liệu yêu cầu (Payload):**
```json
{
    "params": {
        "login": "tên_đăng_nhập",
        "password": "mật_khẩu"
    }
}
```
**Dữ liệu phản hồi (Response):**
```json
{
    "result": {
        "code": 200,
        "data": {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5..."
        }
    }
}
```

---

## 2. API Đợt thu học phí (Tuition Collection)

Đồng bộ hóa thông tin đợt thu học phí, bao gồm danh sách sinh viên và chi tiết các khoản phí.

**URL:** `/api/v1/qldt/tuition_collection`  
**Phương thức:** `POST`

### Cấu trúc yêu cầu
- `action`: `create` (tạo mới/thêm) | `update` (cập nhật) | `delete` (xóa)
- `data`: Đối tượng chứa thông tin chi tiết của đợt thu.

#### Ánh xạ các trường dữ liệu (`data`)
| Trường | Kiểu dữ liệu | Mô tả | Bắt buộc |
| :--- | :--- | :--- | :--- |
| `tuition_collection_id` | string | ID duy nhất từ hệ thống QLDT (không đổi) | Có |
| `code` | string | Mã đợt thu hiển thị trong Odoo | Có |
| `unit_code` | string | Mã đơn vị kinh doanh (VD: "CNTT") | Có |
| `year_id` | string | Mã năm học (khớp với `ma_nam_hoc`) | Có |
| `semester_id` | string | Mã kỳ học (khớp với `ma_ky_hoc`) | Có |
| `description` | string | Ghi chú hoặc mô tả | Không |
| `students` | array | Danh sách sinh viên (xem bên dưới) | Không |

#### Danh sách sinh viên (mảng `students`)
| Trường | Kiểu dữ liệu | Mô tả | Bắt buộc |
| :--- | :--- | :--- | :--- |
| `student_code` | string | Mã sinh viên (khớp với `ma_sinh_vien`) | Có |
| `note` | string | Ghi chú riêng cho từng sinh viên | Không |
| `details` | array | Danh sách chi tiết khoản phí (xem bên dưới) | Không |

#### Chi tiết khoản phí (mảng `details`)
| Trường | Kiểu dữ liệu | Mô tả | Bắt buộc |
| :--- | :--- | :--- | :--- |
| `product_id` | string | Mã khoản thu/sản phẩm (khớp với `default_code`) | Có |
| `amount` | float | Tổng số tiền cần thu | Có |
| `discount` | float | Số tiền miễn giảm | Không |
| `description` | string | Mô tả dòng chi tiết | Không |

### Hành vi của các Action
- **`create`**: 
    - Nếu `tuition_collection_id` chưa tồn tại: Tạo bản ghi mới.
    - Nếu `tuition_collection_id` đã tồn tại: **Thêm mới (append)** sinh viên và chi tiết vào bản ghi hiện có.
- **`update`**: 
    - Thay thế toàn bộ danh sách sinh viên và chi tiết hiện tại bằng danh sách mới được cung cấp.
- **`delete`**: 
    - Xóa bản ghi (chỉ khi chưa được xử lý trong kế toán).

---

## 3. API Thu tiền sinh viên (Student Payment)

Đồng bộ hóa các chứng từ thu tiền của từng sinh viên.

**URL:** `/api/v1/qldt/student_payment`  
**Phương thức:** `POST`

### Cấu trúc yêu cầu
- `action`: `create` | `update` | `delete`
- `data`: Đối tượng chứa thông tin chi tiết phiếu thu.

#### Ánh xạ các trường dữ liệu (`data`)
| Trường | Kiểu dữ liệu | Mô tả | Bắt buộc |
| :--- | :--- | :--- | :--- |
| `student_payment_id` | string | ID chứng từ duy nhất từ QLDT (không đổi) | Có |
| `code` | string | Số chứng từ hiển thị trong Odoo | Có |
| `unit_code` | string | Mã đơn vị kinh doanh | Có |
| `student_code` | string | Mã sinh viên | Có |
| `payment_date` | date | Ngày nộp tiền (YYYY-MM-DD) | Có |
| `accounting_date` | date | Ngày hạch toán (YYYY-MM-DD) | Có |
| `payment_method` | string | `tm` (Tiền mặt) hoặc `tg` (Tiền gửi/Chuyển khoản) | Có |
| `description` | string | Mô tả nội dung thanh toán | Không |
| `details` | array | Danh sách các dòng thanh toán (xem bên dưới) | Không |

#### Chi tiết thanh toán (mảng `details`)
| Trường | Kiểu dữ liệu | Mô tả | Bắt buộc |
| :--- | :--- | :--- | :--- |
| `product_id` | string | Mã khoản thu/sản phẩm | Có |
| `year_id` | string | Mã năm học cho khoản phí này | Có |
| `semester_id` | string | Mã kỳ học cho khoản phí này | Có |
| `amount_total` | float | Tổng số tiền phải nộp | Có |
| `amount_paid` | float | Số tiền thực nộp trong chứng từ này | Có |
| `tuition_collection_id` | string | ID Đợt thu từ QLDT | Không |
| `description` | string | Mô tả nội dung dòng thanh toán | Không |

---

## 4. Các mã phản hồi (Response Codes)

API trả về phản hồi JSON với cấu trúc chuẩn.

| Mã lỗi | Thông báo | Mô tả |
| :--- | :--- | :--- |
| `000` | Thành công | Yêu cầu đã được xử lý thành công |
| `096` | Lỗi hệ thống | Thiếu các trường bắt buộc hoặc lỗi xử lý nội bộ |
| `145` | Thiếu tham số | Thiếu ID định danh từ QLDT (tuition_collection_id hoặc student_payment_id) |
| `147` | Dữ liệu không tồn tại | Không tìm thấy Đơn vị, Sinh viên, Sản phẩm hoặc Bản ghi gốc |
| `500` | Lỗi server | Lỗi hệ thống nghiêm trọng |

**Ví dụ Thành công:**
```json
{
    "result": {
        "code": "000",
        "message": "Đồng bộ thành công",
        "data": { "code": "000" }
    }
}
```

**Ví dụ Lỗi:**
```json
{
    "result": {
        "code": "147",
        "message": "Không tìm thấy Business Unit với mã: CNTT"
    }
}
```
