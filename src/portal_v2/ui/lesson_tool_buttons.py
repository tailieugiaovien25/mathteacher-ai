"""Icons for actions in the lesson designer's tool tabs."""

TOOL_ICONS = {
    "Mở": "folder_open", "Lưu": "save", "Bài mới": "note_add",
    "Nạp": "upload_file", "Tải bản nháp JSON": "download",
    "Chọn bài này": "check_circle", "AI đề xuất thẻ hoạt động": "auto_awesome",
    "Duyệt và thêm vào bài": "task_alt", "Bổ sung phương án từ câu hỏi đã duyệt": "playlist_add",
    "Bỏ thẻ khỏi bài": "delete", "Lưu chỉnh sửa": "save",
    "Tìm trang": "search", "Lấy nội dung": "content_copy", "Lưu nguồn": "save",
    "Thêm nhân vật vào hoạt động này": "person_add", "Bỏ nhân vật khỏi hoạt động": "person_remove",
    "Thêm công cụ vào hoạt động này": "add_circle", "Mở sân khấu": "open_in_new",
    "Tải sân khấu HTML": "download", "Bỏ công cụ khỏi hoạt động": "delete",
    "Chuẩn bị sân khấu tích hợp": "build_circle",
    "Thêm slide vào hoạt động này": "add_to_photos", "Xóa khối": "delete_outline",
    "Thêm khối nội dung": "post_add", "Xóa slide đang chọn": "delete",
    "Thêm thẻ ghi nhận vào hoạt động": "add_circle", "Lưu lần ghi nhận": "save",
    "Lưu ảnh vào thẻ": "add_photo_alternate", "Bỏ ảnh này": "delete_outline",
    "Bật hộp nhận ảnh nội bộ": "wifi_tethering", "Tạo mã ghép cặp mới": "qr_code_2",
    "Làm mới hộp chờ": "refresh", "Duyệt và đưa ảnh vào thẻ": "verified",
    "Bỏ ảnh chờ": "delete_outline", "Dừng hộp nhận ảnh": "stop_circle",
    "Bỏ thẻ ghi nhận": "delete",
}


def tool_button(target, label: str, **kwargs):
    """Keep the action label and behavior while adding its Material icon."""
    return target.button(label, icon=":material/" + TOOL_ICONS[label] + ":", **kwargs)


def tool_download_button(target, label: str, data, **kwargs):
    return target.download_button(label, data, icon=":material/" + TOOL_ICONS[label] + ":", **kwargs)
