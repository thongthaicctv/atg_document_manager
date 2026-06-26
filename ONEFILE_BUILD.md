# Đóng gói onefile

## Server cài cho người dùng

Chạy:

```bat
build_server_onefile.bat
```

Kết quả:

```text
dist\ATG_Document_Manager_Server.exe
```

Khi triển khai máy người dùng:

1. Copy `ATG_Document_Manager_Server.exe` vào thư mục cài đặt, ví dụ `D:\ATG_DOCUMENT\server`.
2. Nếu đã có cấu hình/license, đặt `config.json` và `license.key` cùng thư mục với file exe.
3. Chạy exe để mở server.
4. Nếu chưa có license, đăng nhập root, vào `Cấu hình hệ thống`, lấy `Mã máy hiện tại`, phát hành license và gắn lại trên màn hình đó.

Lưu ý: Không copy private key phát hành license sang máy người dùng.

## License tool

Chạy:

```bat
build_license_tool_onefile.bat
```

Kết quả:

```text
dist\ATG_License_Tool.exe
```

Mật khẩu mở tool:

```text
antn@2016
```

Private key mặc định:

```text
D:\ATG_DOCUMENT\license\atg_license_private.json
```

Ví dụ phát hành license:

```bat
ATG_License_Tool.exe issue --machine-code "A903-8B16-1804-9AD7-86FB-BB20-EA5C-938C" --customer "Ban kỹ thuật" --expires 2036-12-31 --output license.key
```

Ví dụ xem mã máy:

```bat
ATG_License_Tool.exe machine
```
