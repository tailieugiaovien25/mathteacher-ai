from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / (
    "src/portal_v2/ui/"
    "admin_lesson_plan_coordination_center_streamlit.py"
)


def _text():
    return UI.read_text(encoding="utf-8-sig")


def test_structured_editor_fields_are_present():
    text = _text()
    for token in [
        "Tên mẫu giáo án",
        "Phông chữ",
        "Cỡ chữ nội dung",
        "Giãn dòng",
        "Số ngày soạn trước thứ Hai",
        "Số ngày duyệt trước thứ Hai",
        "Nhãn phê duyệt",
        "Căn khối phê duyệt",
    ]:
        assert token in text


def test_structured_payload_preserves_runtime_sections():
    text = _text()
    assert 'payload["template_profile"] = template_profile' in text
    assert 'payload["date_policy"] = date_policy' in text
    assert 'payload["approval_policy"] = approval_policy' in text


def test_json_is_advanced_only():
    text = _text()
    assert "Cấu hình nâng cao (JSON)" in text
    assert "JSON nâng cao" in text
    assert "Nâng cao: xem/chỉnh JSON" not in text


def test_create_new_version_and_update_use_structured_editor():
    text = _text()
    assert text.count("_render_structured_configuration_editor(") >= 4
    assert text.count("_build_configuration_payload_from_editor(") >= 4
