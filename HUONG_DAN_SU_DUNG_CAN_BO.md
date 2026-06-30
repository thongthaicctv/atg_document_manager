# Hướng dẫn sử dụng ATG Document Manager cho tài khoản Cán bộ

Phiên bản tài liệu: 30/06/2026

Tài liệu này dành cho người dùng có vai trò **Cán bộ** trong hệ thống quản lý văn bản nội bộ. Nội dung tập trung vào các thao tác hằng ngày: đăng nhập, tiếp nhận văn bản, tạo văn bản đề xuất đi, tìm kiếm, upload/scan tài liệu, cập nhật trạng thái và phân quyền xử lý.

## 1. Khái niệm cần nắm

### 1.1. Văn bản nhận về

Là các văn bản/công văn/hồ sơ được đơn vị khác gửi đến. Khi nhập văn bản nhận về, cán bộ cần chọn **Hướng xử lý**:

- **Lưu hồ sơ**: văn bản chỉ lưu lại, không cần tạo văn bản đề xuất đi.
- **Cần phúc đáp**: văn bản cần có phản hồi.
- **Cần làm đề xuất**: văn bản cần lập đề xuất xử lý.
- **Cần làm báo cáo**: văn bản cần lập báo cáo.
- **Khác**: trường hợp xử lý ngoài các nhóm trên.

Văn bản nhận về không cập nhật trạng thái thủ công. Trạng thái của văn bản nhận về được hệ thống tự hiển thị theo ngày nhận hoặc theo văn bản đề xuất đi liên quan.

### 1.2. Văn bản đề xuất đi

Là văn bản do cán bộ lập để xử lý công việc. Văn bản đề xuất đi có thể thuộc một trong hai trường hợp:

- **Có liên quan văn bản nhận về**: chọn văn bản nhận về liên quan trong ô “Chuyển văn bản nhận về liên quan”.
- **Không phát sinh từ văn bản nhận về**: chọn “Khác / không phát sinh từ văn bản nhận về”.

Văn bản đề xuất đi có luồng trạng thái xử lý riêng như: mới tạo, đã trình lãnh đạo, lãnh đạo đã duyệt, yêu cầu chỉnh sửa, đã chỉnh sửa bổ sung, đã ban hành/phát hành, đã lưu hồ sơ hoặc không tiếp tục thực hiện.

### 1.3. Quyền của tài khoản Cán bộ

Tài khoản cán bộ thường có thể:

- Xem Dashboard.
- Tìm kiếm và xem chi tiết văn bản.
- Tạo văn bản nhận về.
- Tạo văn bản đề xuất đi.
- Upload file hoặc scan tài liệu cho văn bản do mình có quyền.
- Cập nhật trạng thái văn bản đề xuất đi khi có quyền.
- Phân quyền tiếp cho cán bộ khác khi được cấp quyền chia sẻ.

Tài khoản cán bộ không có quyền:

- Xóa văn bản.
- Xóa file đính kèm.
- Quản lý tài khoản hệ thống.
- Cấu hình hệ thống, database, license, port, phòng ban hoặc phân loại văn bản.
- Xuất báo cáo quản trị nếu không được phân quyền bởi admin/root.

## 2. Đăng nhập và đăng xuất

### 2.1. Đăng nhập

1. Mở trình duyệt Chrome hoặc Edge.
2. Truy cập địa chỉ do quản trị cung cấp, ví dụ:
   - Trên máy server: `http://localhost:8088`
   - Trong mạng LAN: `http://IP-MAY-SERVER:8088`
3. Nhập **Tên đăng nhập**.
4. Nhập **Mật khẩu**.
5. Bấm **Đăng nhập**.

Nếu đăng nhập không thành công, kiểm tra lại tên đăng nhập/mật khẩu hoặc liên hệ quản trị để mở khóa/cấp lại mật khẩu.

### 2.2. Đăng xuất

1. Nhìn góc dưới bên trái màn hình.
2. Bấm biểu tượng đăng xuất.
3. Đóng trình duyệt nếu không dùng tiếp.

Nên đăng xuất khi dùng máy tính chung.

### 2.3. Tự đổi mật khẩu cá nhân

Cán bộ có thể tự đổi mật khẩu đăng nhập của chính mình mà không cần nhờ admin.

Các bước thực hiện:

1. Đăng nhập vào hệ thống.
2. Nhìn khu vực tài khoản ở góc dưới bên trái màn hình.
3. Bấm biểu tượng **chìa khóa** để mở màn hình **Đổi mật khẩu cá nhân**.
4. Nhập **Mật khẩu hiện tại**.
5. Nhập **Mật khẩu mới**.
6. Nhập lại mật khẩu mới tại ô **Nhập lại mật khẩu mới**.
7. Bấm **Đổi mật khẩu**.

Lưu ý:

- Mật khẩu hiện tại phải nhập đúng.
- Mật khẩu mới phải đạt độ dài tối thiểu theo cấu hình hệ thống.
- Mật khẩu mới không được trùng với mật khẩu đang dùng.
- Sau khi đổi thành công, lần đăng nhập tiếp theo phải dùng mật khẩu mới.

## 3. Tổng quan các menu của Cán bộ

### 3.1. Dashboard

Màn hình tổng quan nhanh tình hình xử lý văn bản.

Các ô thống kê có thể bấm để mở nhanh danh sách tương ứng:

- **Tổng văn bản**: tổng số văn bản nhận về và văn bản đề xuất đi.
- **Tổng văn bản cần xử lý**: số văn bản nhận về có hướng xử lý cần tiếp tục nhưng chưa có văn bản đề xuất đi liên quan.
- **Hồ sơ lưu không cần xử lý**: văn bản nhận về có hướng xử lý “Lưu hồ sơ”.
- **Văn bản mới tạo**: văn bản đề xuất đi được tạo trong ngày.
- **Đã trình lãnh đạo**: văn bản đề xuất đi đang ở trạng thái đã trình lãnh đạo.
- **Yêu cầu chỉnh sửa**: văn bản đề xuất đi đang bị yêu cầu chỉnh sửa.
- **Đã chỉnh sửa bổ sung**: văn bản đề xuất đi đã được chỉnh sửa sau yêu cầu.
- **Lãnh đạo đã duyệt**: văn bản đề xuất đi đã được lãnh đạo duyệt.
- **Đã ban hành / đã phát hành**: văn bản đề xuất đi đã ban hành/phát hành.
- **Đã lưu hồ sơ**: văn bản đề xuất đi đã lưu hồ sơ.
- **Không tiếp tục thực hiện**: văn bản đề xuất đi đã dừng xử lý.

### 3.2. Quản lý và tìm kiếm văn bản

Màn hình dùng để tìm kiếm tổng hợp cả văn bản nhận về và văn bản đề xuất đi.

Các bộ lọc thường dùng:

- **Tìm kiếm nhanh**: nhập số thứ tự, số/ký hiệu hoặc tiêu đề.
- **Từ ngày / Đến ngày**: lọc theo khoảng thời gian.
- **Số/ký hiệu**: thường dùng cho văn bản nhận về.
- **Tiêu đề**: tìm theo tên văn bản.
- **Người nhận/đề xuất**: tìm theo người phụ trách.
- **Người tạo**: tìm theo người nhập hồ sơ.
- **Đơn vị gửi đến**: lọc văn bản nhận về.
- **Đơn vị nhận văn bản**: lọc văn bản đề xuất đi.
- **Trạng thái**: lọc theo trạng thái hiện tại.
- **Phân loại văn bản**: lọc theo loại văn bản đã cấu hình.

Bấm **Lọc** để tìm kiếm. Bấm **Xóa lọc** để quay về danh sách ban đầu.

### 3.3. Văn bản nhận về

Menu dùng để nhập, xem và theo dõi văn bản/công văn được gửi đến.

### 3.4. Văn bản đề xuất đi

Menu dùng để tạo và xử lý các văn bản đề xuất đi. Đây là nơi cập nhật trạng thái xử lý, upload tài liệu bổ sung, scan PDF và theo dõi timeline.

### 3.5. Hướng dẫn sử dụng

Menu nằm ở cuối danh sách menu chính, dùng để mở nhanh tài liệu hướng dẫn thao tác cho cán bộ ngay trong phần mềm. Khi cần xem lại cách tạo văn bản, scan tài liệu, cập nhật trạng thái hoặc phân quyền xử lý, bấm **Hướng dẫn sử dụng** để tra cứu.

## 4. Tạo văn bản nhận về

### 4.1. Mở màn hình tạo

1. Vào menu **Văn bản nhận về**.
2. Bấm **Tạo văn bản nhận về**.

### 4.2. Nhập thông tin

Các trường chính:

- **Số thứ tự**: hệ thống tự sinh, không cần nhập.
- **Số/ký hiệu**: nhập số/ký hiệu trên văn bản gửi đến. Trường này bắt buộc.
- **Hướng xử lý**: chọn hướng xử lý phù hợp. Trường này bắt buộc.
- **Mức độ ưu tiên**: chọn Bình thường, Khẩn hoặc Rất khẩn.
- **Ngày nhận**: nhập ngày nhận văn bản.
- **Giờ nhận**: nhập giờ nhận nếu cần ghi nhận chính xác.
- **Tiêu đề**: nhập tiêu đề văn bản. Trường này bắt buộc.
- **Trích yếu**: nhập tóm tắt ngắn nội dung văn bản.
- **Nội dung**: nhập nội dung chính hoặc mô tả xử lý.
- **Người nhận văn bản / người đề xuất**: hệ thống tự lấy theo tài khoản đang đăng nhập, không chỉnh sửa.
- **Đơn vị gửi đến**: chọn đơn vị gửi văn bản. Trường này bắt buộc.
- **File đính kèm**: chọn một hoặc nhiều file nếu có.
- **Scan văn bản sang PDF**: chụp/chọn nhiều trang để hệ thống ghép thành một file PDF.

### 4.3. Chọn hướng xử lý đúng nghiệp vụ

Chọn **Lưu hồ sơ** khi văn bản chỉ cần lưu lại, không cần lập văn bản đề xuất đi.

Chọn **Cần phúc đáp**, **Cần làm đề xuất**, **Cần làm báo cáo** hoặc **Khác** khi văn bản cần tiếp tục xử lý. Các văn bản này sẽ được tính vào nhóm **Tổng văn bản cần xử lý** cho đến khi có văn bản đề xuất đi liên quan.

### 4.4. Lưu văn bản

1. Kiểm tra lại các trường bắt buộc.
2. Bấm **Lưu**.
3. Sau khi lưu thành công, hệ thống chuyển sang màn hình chi tiết văn bản.

## 5. Tạo văn bản đề xuất đi

### 5.1. Mở màn hình tạo

1. Vào menu **Văn bản đề xuất đi**.
2. Bấm **Tạo văn bản đề xuất đi**.

### 5.2. Chọn văn bản nhận về liên quan

Tại ô **Chuyển văn bản nhận về liên quan**:

- Nếu đề xuất đi được lập để xử lý một văn bản nhận về, chọn đúng văn bản nhận về trong danh sách.
- Nếu đề xuất đi là hồ sơ độc lập, chọn **Khác / không phát sinh từ văn bản nhận về**.

Khi chọn văn bản nhận về liên quan, trạng thái/thống kê của văn bản nhận về sẽ được cập nhật theo quá trình xử lý văn bản đề xuất đi.

### 5.3. Nhập thông tin văn bản đề xuất đi

Các trường chính:

- **Số thứ tự**: hệ thống tự sinh, không cần nhập.
- **Chuyển văn bản nhận về liên quan**: chọn văn bản liên quan hoặc chọn Khác.
- **Phân loại văn bản**: chọn loại văn bản như Báo cáo, Tờ trình, Đề xuất... Trường này bắt buộc.
- **Mức độ ưu tiên**: chọn mức độ xử lý.
- **Ngày hết hạn**: nhập nếu văn bản có hạn xử lý; nếu không có hạn thì để trống.
- **Tiêu đề**: nhập tiêu đề văn bản. Trường này bắt buộc.
- **Trích yếu**: nhập tóm tắt nội dung.
- **Nội dung**: nhập nội dung đề xuất/xử lý.
- **Người nhận văn bản / người đề xuất**: hệ thống tự lấy theo tài khoản đang đăng nhập, không chỉnh sửa.
- **Đơn vị nhận văn bản**: chọn đơn vị nhận văn bản. Trường này bắt buộc.
- **File đính kèm**: chọn một hoặc nhiều file nếu có.
- **Scan văn bản sang PDF**: chụp/chọn nhiều trang để hệ thống ghép thành PDF.

### 5.4. Lưu văn bản đề xuất đi

1. Kiểm tra phân loại văn bản và đơn vị nhận văn bản.
2. Bấm **Lưu**.
3. Văn bản mới tạo ban đầu có trạng thái **Mới tạo đề xuất**.

## 6. Xem chi tiết văn bản

Từ danh sách văn bản, có thể mở chi tiết bằng một trong hai cách:

- Bấm vào **tiêu đề văn bản**.
- Bấm biểu tượng **mắt** ở cột thao tác.

Màn hình chi tiết hiển thị:

- Thông tin văn bản.
- Số thứ tự.
- Số/ký hiệu nếu là văn bản nhận về.
- Phân loại văn bản.
- Hướng xử lý hoặc văn bản nhận về liên quan.
- Ngày nhận/giờ nhận hoặc ngày hết hạn.
- Người nhận/người đề xuất.
- Đơn vị gửi đến hoặc đơn vị nhận văn bản.
- Người tạo/chủ văn bản.
- Lãnh đạo/người cho ý kiến.
- Trích yếu và nội dung.
- File đính kèm.
- Mốc xử lý.
- Phân quyền xử lý.
- Timeline lịch sử thao tác.

## 7. Upload file và scan tài liệu

### 7.1. Upload nhiều file

Ở màn hình tạo mới, màn hình chi tiết hoặc cập nhật trạng thái:

1. Bấm **Chọn tệp**.
2. Chọn một hoặc nhiều file.
3. Có thể chọn các định dạng: PDF, JPG, JPEG, PNG, DOC, DOCX, XLS, XLSX.
4. Khi đang ở màn hình chi tiết, bấm **Upload** để tải file lên.
5. Khi đang ở màn hình tạo/cập nhật, bấm **Lưu** hoặc **Cập nhật** để lưu kèm file.

### 7.2. Scan nhiều trang sang PDF

Chức năng scan dùng để ghép nhiều ảnh thành một file PDF.

Các cách sử dụng:

- Bấm **Mở camera** hoặc **Chụp/chọn trang** để chụp từng trang.
- Bấm **Chọn tệp** trong khung scan để chọn nhiều ảnh đã chụp sẵn.
- Sau khi chọn/chụp, hệ thống hiển thị số trang đã chọn.
- Có thể xóa từng trang hoặc xóa toàn bộ trang đã chọn.
- Khi lưu văn bản/cập nhật trạng thái, hệ thống tự ghép các ảnh thành một file PDF.

### 7.3. Lưu ý khi dùng camera

Trình duyệt có quy định bảo mật riêng:

- Trên chính máy server, nên mở bằng `http://localhost:PORT` để dùng webcam trực tiếp.
- Khi truy cập qua IP LAN như `http://192.168.x.x:PORT`, Chrome/Edge có thể không cho mở webcam trực tiếp.
- Muốn dùng webcam trực tiếp qua LAN, quản trị cần cấu hình HTTPS cho server.
- Nếu chưa có HTTPS, vẫn có thể dùng nút **Chọn tệp** hoặc nút **Chụp/chọn trang** trên điện thoại để dùng camera hệ thống rồi upload ảnh.

## 8. Cập nhật trạng thái văn bản đề xuất đi

Chỉ văn bản đề xuất đi mới cập nhật trạng thái thủ công. Văn bản nhận về tự cập nhật trạng thái theo văn bản đề xuất đi liên quan.

### 8.1. Mở màn hình cập nhật trạng thái

1. Mở chi tiết văn bản đề xuất đi.
2. Bấm **Trạng thái**.

Nếu không thấy nút **Trạng thái**, tài khoản chưa có quyền cập nhật trạng thái cho văn bản đó.

### 8.2. Nhập thông tin cập nhật

Các trường cần chú ý:

- **Trạng thái mới**: chọn trạng thái xử lý.
- **Tên lãnh đạo/người cho ý kiến**: bắt buộc nhập.
- **Ngày thực tế**: nhập ngày thực hiện nếu cần ghi nhận mốc thực tế.
- **Ghi chú xử lý**: nhập nội dung xử lý, ý kiến lãnh đạo hoặc ghi chú cần lưu.
- **File bổ sung**: upload một hoặc nhiều file bổ sung nếu có.
- **Scan văn bản bổ sung sang PDF**: scan thêm hồ sơ, phiếu trình, bản ký, tài liệu bổ sung...

### 8.3. Các trạng thái thường dùng

- **Đã trình lãnh đạo**: đã trình hồ sơ lên lãnh đạo/người cho ý kiến.
- **Lãnh đạo đã duyệt**: lãnh đạo đã đồng ý/duyệt.
- **Lãnh đạo yêu cầu chỉnh sửa**: hồ sơ cần sửa lại.
- **Đã chỉnh sửa bổ sung**: đã hoàn thiện sau khi bị yêu cầu chỉnh sửa.
- **Đã ban hành / đã phát hành**: văn bản đã phát hành chính thức.
- **Đã lưu hồ sơ**: đã hoàn tất và lưu hồ sơ.
- **Không tiếp tục thực hiện**: dừng xử lý hồ sơ.

Sau khi bấm **Cập nhật**, hệ thống lưu lại trạng thái mới và ghi timeline lịch sử.

## 9. Phân quyền xử lý cho cán bộ khác

Người tạo/chủ văn bản hoặc người được cấp quyền chia sẻ có thể phân quyền cho cán bộ khác.

### 9.1. Mở màn hình phân quyền

1. Mở chi tiết văn bản.
2. Bấm **Phân quyền**.

Nếu không thấy nút **Phân quyền**, tài khoản chưa được cấp quyền chia sẻ văn bản đó.

### 9.2. Cấp quyền cho một hoặc nhiều cán bộ

1. Tại ô **Chọn user**, chọn một hoặc nhiều tài khoản cán bộ.
2. Trên máy tính, dùng Ctrl hoặc Shift để chọn nhiều người.
3. Trên điện thoại, chạm chọn từng tài khoản nếu trình duyệt hỗ trợ.
4. Tick các quyền cần cấp:
   - **Quyền xem**: xem chi tiết văn bản.
   - **Quyền sửa**: chỉnh sửa thông tin văn bản.
   - **Cập nhật trạng thái**: cập nhật trạng thái văn bản đề xuất đi.
   - **Upload file/scan PDF**: bổ sung file hoặc scan tài liệu.
   - **Phân quyền tiếp**: cho phép cấp quyền lại cho cán bộ khác.
5. Nhập ghi chú nếu cần.
6. Bấm **Lưu phân quyền**.

### 9.3. Thu hồi quyền

Trong bảng **User được phân quyền**:

1. Tìm cán bộ cần thu hồi.
2. Bấm biểu tượng thu hồi.
3. Xác nhận thao tác.

Lưu ý: root và admin có toàn quyền hệ thống nên không hiển thị trong danh sách phân quyền cán bộ.

## 10. Theo dõi timeline lịch sử

Timeline nằm ở màn hình chi tiết văn bản.

Timeline ghi lại:

- Ai tạo văn bản.
- Ai upload file.
- Ai cập nhật trạng thái.
- Trạng thái cũ và trạng thái mới.
- Tên lãnh đạo/người cho ý kiến.
- Ghi chú xử lý.
- Thời gian thực hiện.

Khi cần tra cứu quá trình xử lý, nên xem timeline trước để biết hồ sơ đã qua các bước nào.

## 11. Tải file đính kèm

1. Mở chi tiết văn bản.
2. Tìm phần **File đính kèm**.
3. Bấm tên file hoặc biểu tượng tải xuống.
4. File sẽ được tải về máy.

Tài khoản cán bộ không được xóa file, trừ khi quản trị thay đổi nghiệp vụ hệ thống.

## 12. Các lỗi thường gặp và cách xử lý

### 12.1. Không lưu được văn bản

Kiểm tra các trường bắt buộc:

- Văn bản nhận về phải có số/ký hiệu, hướng xử lý, tiêu đề và đơn vị gửi đến.
- Văn bản đề xuất đi phải có phân loại văn bản, tiêu đề và đơn vị nhận văn bản.
- File upload không được vượt quá dung lượng cho phép.

### 12.2. Không thấy danh sách phân loại hoặc phòng ban

Nguyên nhân thường là quản trị chưa cấu hình dữ liệu.

Cách xử lý: báo admin/root bổ sung tại menu **Phân loại văn bản** hoặc **Phân loại phòng ban**.

### 12.3. Không mở được camera khi truy cập bằng IP LAN

Nguyên nhân: Chrome/Edge chặn webcam trên địa chỉ HTTP qua LAN.

Cách xử lý:

- Dùng `localhost` nếu đang thao tác trên máy server.
- Hoặc cấu hình HTTPS.
- Hoặc dùng nút chọn tệp/chụp ảnh bằng camera hệ thống rồi upload.

### 12.4. Không thấy nút Sửa, Trạng thái, Upload hoặc Phân quyền

Nguyên nhân: tài khoản chưa có quyền thao tác trên văn bản đó.

Cách xử lý: liên hệ người tạo/chủ văn bản hoặc quản trị để được phân quyền.

### 12.5. Văn bản nhận về không có nút cập nhật trạng thái

Đây là nghiệp vụ đúng của hệ thống. Văn bản nhận về tự cập nhật trạng thái theo ngày nhận hoặc theo văn bản đề xuất đi liên quan.

### 12.6. Không đổi được mật khẩu cá nhân

Kiểm tra lại các nguyên nhân sau:

- Nhập sai mật khẩu hiện tại.
- Mật khẩu mới quá ngắn.
- Mật khẩu mới và ô nhập lại mật khẩu mới không giống nhau.
- Mật khẩu mới trùng với mật khẩu đang dùng.

Nếu vẫn không đổi được, liên hệ admin/root để kiểm tra trạng thái tài khoản.

## 13. Quy trình khuyến nghị hằng ngày

### 13.1. Khi nhận một văn bản mới

1. Vào **Văn bản nhận về**.
2. Tạo văn bản nhận về.
3. Nhập số/ký hiệu, ngày giờ nhận, tiêu đề, hướng xử lý và đơn vị gửi đến.
4. Upload hoặc scan tài liệu gốc.
5. Nếu hướng xử lý là **Lưu hồ sơ**, kết thúc tại đây.
6. Nếu cần xử lý tiếp, tạo văn bản đề xuất đi liên quan.

### 13.2. Khi cần lập đề xuất xử lý

1. Vào **Văn bản đề xuất đi**.
2. Tạo văn bản đề xuất đi.
3. Chọn văn bản nhận về liên quan nếu có.
4. Chọn phân loại, đơn vị nhận văn bản, tiêu đề và nội dung.
5. Upload/scan tài liệu nếu có.
6. Lưu văn bản.
7. Cập nhật trạng thái khi trình lãnh đạo hoặc khi có kết quả xử lý.

### 13.3. Khi lãnh đạo cho ý kiến

1. Mở văn bản đề xuất đi.
2. Bấm **Trạng thái**.
3. Chọn trạng thái phù hợp.
4. Nhập tên lãnh đạo/người cho ý kiến.
5. Nhập ghi chú xử lý.
6. Upload hoặc scan tài liệu bổ sung nếu có.
7. Bấm **Cập nhật**.

### 13.4. Khi cần chuyển người khác xử lý cùng

1. Mở chi tiết văn bản.
2. Bấm **Phân quyền**.
3. Chọn cán bộ cần cấp quyền.
4. Chọn đúng quyền cần cấp.
5. Bấm **Lưu phân quyền**.

## 14. Lưu ý bảo mật và sử dụng đúng cách

- Không chia sẻ tài khoản/mật khẩu cho người khác.
- Nên đổi mật khẩu cá nhân định kỳ hoặc ngay khi nghi ngờ bị lộ mật khẩu.
- Đăng xuất khi không dùng máy tính cá nhân.
- Kiểm tra kỹ văn bản trước khi cập nhật trạng thái.
- Không upload file không liên quan đến hồ sơ.
- Khi scan nhiều trang, nên kiểm tra thứ tự trang trước khi lưu.
- Không tự ý tạo văn bản đề xuất đi liên quan sai văn bản nhận về.
- Nếu nhập sai hồ sơ quan trọng, báo quản trị/root để được hỗ trợ xử lý.
