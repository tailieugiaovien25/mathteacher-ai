from pathlib import Path


SOURCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "portal_v2"
    / "ui"
    / "weekly_schedule_streamlit.py"
)


def test_standardization_action_labels_use_safe_unicode_escapes():
    text = SOURCE_PATH.read_text(encoding="utf-8")
    expected = (
        r'"\U0001f4e4 Up gi\u00e1o \u00e1n"',
        r'"\u2728 T\u1ea1o gi\u00e1o \u00e1n chu\u1ea9n"',
        r'"\U0001f441 Xem tr\u01b0\u1edbc"',
        r'"\U0001f4be L\u01b0u"',
        r'"\U0001f4e5 T\u1ea3i xu\u1ed1ng"',
    )
    for label in expected:
        assert label in text


def test_standardization_action_keys_are_preserved():
    text = SOURCE_PATH.read_text(encoding="utf-8")
    keys = (
        "standardization_action_upload",
        "standardization_action_create",
        "standardization_action_preview",
        "standardization_action_save",
        "standardization_action_download",
    )
    for key in keys:
        assert key in text


def test_corrupted_action_labels_are_removed():
    text = SOURCE_PATH.read_text(encoding="utf-8")
    start = text.index(
        "def _render_standardization_action_flow("
    )
    end = text.index("\ndef ", start + 5)
    section = text[start:end]

    assert "?? Up gi?o ?n" not in section
    assert "?? T?o gi?o ?n chu?n" not in section
    assert "??? Xem tr??c" not in section
    assert "?? L?u" not in section
    assert "?? T?i xu?ng" not in section
