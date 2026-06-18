# ATG Document Manager

Phần mềm web quản lý văn bản, công văn và giấy tờ đề xuất nội bộ theo yêu cầu trong `codex.docx`.

## Cài đặt nhanh trên Windows

1. Tạo database user MariaDB có quyền tạo database hoặc tạo sẵn database `atg_document_system` với charset `utf8mb4`.
2. Sửa `config.json`, đặc biệt là thông tin MariaDB, `security.secret_key` và `storage.upload_dir`.
3. Cài thư viện:

```bat
pip install -r requirements.txt
```

4. Nếu chưa tạo user/database trong MariaDB, chạy bằng tài khoản root MariaDB:

```bat
setup_mariadb.bat
```

Lệnh này đọc trực tiếp `config.json` để tạo đúng database, user và password đang cấu hình.

5. Khởi tạo bảng và tài khoản root:

```bat
.\.venv\Scripts\python.exe init_db.py
```

6. Chạy ứng dụng:

```bat
run_server.bat
```

Hoặc:

```bat
uvicorn app.main:app --host 0.0.0.0 --port 8088
```

Nếu đã activate môi trường ảo `.venv`, có thể dùng `python init_db.py` và `python -m app.main`.

Tài khoản mặc định lần đầu:

- Username: `root`
- Password: `admin@123`

Sau khi đăng nhập lần đầu nên đổi mật khẩu root và thay `security.secret_key` trong `config.json`.
# atg_document_manager
