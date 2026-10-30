from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from portal_v2.ui.teaching_assistant_avatar_surface_streamlit import build_avatar_surface_html


def test_avatar_surface_contains_identity_and_state():
    html = build_avatar_surface_html(
        avatar_svg="<svg><circle cx='10' cy='10' r='10'/></svg>",
        display_name="Trợ giảng Toán",
        state="speaking",
    )
    assert "Trợ giảng Toán" in html
    assert "speaking" in html
    assert "class='avatar'" in html


def test_avatar_surface_is_presentation_only():
    html = build_avatar_surface_html(
        avatar_svg="<svg></svg>",
        display_name="Trợ giảng Toán",
        state="listening",
    )
    assert "Quyền điều khiển lớp học vẫn thuộc Kernel/Policy" in html
    assert "classroom.slide.open" not in html


def test_avatar_surface_escapes_script_closing_sequences_in_ai_text():
    html = build_avatar_surface_html(
        avatar_svg="<svg></svg>",
        display_name="Trợ giảng Toán",
        state="speaking",
        speech_text="Nội dung </script><script>alert(1)</script>",
    )
    assert "Nội dung </script>" not in html
    assert "\\u003c/script\\u003e" in html


def test_teacher_navigation_exposes_teaching_assistant():
    from portal_v2.ui.workspace_navigation import route_from_label
    route = route_from_label("AI Trợ giảng")
    assert route.route_id == "ai_teaching_assistant"
    assert route.group == "Lớp học"


if __name__ == "__main__":
    test_avatar_surface_contains_identity_and_state()
    test_avatar_surface_is_presentation_only()
    test_teacher_navigation_exposes_teaching_assistant()
    print("3/3 PASS")
