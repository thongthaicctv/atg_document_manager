DOCUMENT_STATUSES = {
    "new_draft": "Mới tạo đề xuất",
    "submitted_to_leader": "Đã trình lãnh đạo",
    "leader_approved": "Lãnh đạo đã duyệt",
    "need_revision": "Lãnh đạo yêu cầu chỉnh sửa",
    "revised": "Đã chỉnh sửa bổ sung",
    "issued": "Đã ban hành / đã phát hành",
    "archived": "Đã lưu hồ sơ",
    "cancelled": "Không tiếp tục thực hiện",
}

INCOMING_DOCUMENT_STATUSES = {
    "new_received": "Mới nhận",
    "received": "Đã nhận",
}

STATUS_BADGE_CLASSES = {
    "new_draft": "text-bg-secondary",
    "submitted_to_leader": "text-bg-primary",
    "leader_approved": "text-bg-success",
    "need_revision": "text-bg-warning",
    "revised": "text-bg-info",
    "issued": "text-bg-dark",
    "archived": "text-bg-success",
    "cancelled": "text-bg-danger",
}

INCOMING_STATUS_BADGE_CLASSES = {
    "new_received": "text-bg-info",
    "received": "text-bg-secondary",
}

DOCUMENT_PRIORITIES = {
    "normal": "Bình thường",
    "urgent": "Khẩn",
    "very_urgent": "Rất khẩn",
}

INCOMING_ACTIONS = {
    "archive": "Lưu hồ sơ",
    "need_reply": "Cần phúc đáp",
    "need_proposal": "Cần làm đề xuất",
    "need_report": "Cần làm báo cáo",
    "other": "Khác",
}

USER_ROLES = {
    "root": "Root",
    "admin": "Quản trị",
    "user": "Cán bộ",
}

USER_STATUSES = {
    "active": "Đang hoạt động",
    "locked": "Đã khóa",
    "disabled": "Vô hiệu hóa",
}

LOG_ACTIONS = {
    "create_document": "Tạo văn bản",
    "update_document": "Cập nhật văn bản",
    "update_status": "Cập nhật trạng thái",
    "upload_file": "Upload file",
    "delete_file": "Xóa file",
    "grant_permission": "Cấp quyền",
    "revoke_permission": "Thu hồi quyền",
    "update_permission": "Cập nhật quyền",
    "login": "Đăng nhập",
    "logout": "Đăng xuất",
}
