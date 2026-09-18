import inspect

from portal_v2.ui import assessment_builder_streamlit as ui


def test_ui_contract_is_math69_source_only() -> None:
    assert ui.ASSESSMENT_BUILDER_TITLE == "Tạo đề kiểm tra Toán 6–9"
    assert ui.ASSESSMENT_BUILDER_READ_ONLY is True
    assert ui.ASSESSMENT_BUILDER_DATABASE_WRITE is False
    assert ui.ASSESSMENT_BUILDER_PRODUCTION_ROUTE_CHANGE is False

    signature = inspect.signature(ui.render_assessment_builder_page)
    assert tuple(signature.parameters) == ("st", "initial_grade_level")
    assert "client" not in signature.parameters
    assert "user_id" not in signature.parameters


def test_ui_source_has_no_supabase_or_database_calls() -> None:
    source = inspect.getsource(ui.render_assessment_builder_page)
    assert ".rpc(" not in source
    assert ".table(" not in source
    assert "client." not in source
