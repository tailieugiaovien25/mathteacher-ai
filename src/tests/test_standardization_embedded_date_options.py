import inspect
from types import SimpleNamespace

import portal_v2.ui.weekly_schedule_streamlit as module


class FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.labels = []

    def markdown(self, value):
        self.labels.append(value)

    def checkbox(self, label, *, key, **kwargs):
        self.labels.append(label)
        return bool(self.session_state.get(key, False))

    def number_input(self, label, *, key, value, **kwargs):
        self.labels.append(label)
        self.session_state.setdefault(key, value)
        return self.session_state[key]


def test_date_and_document_controls_have_required_defaults(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(module, "st", fake)

    module._render_standardization_date_and_document_options()

    assert fake.session_state[module._MT_DRAFTING_ENABLED] is True
    assert fake.session_state[module._MT_DRAFTING_DAYS] == 3
    assert fake.session_state[module._MT_APPROVAL_ENABLED] is True
    assert fake.session_state[module._MT_APPROVAL_DAYS] == 1
    assert fake.session_state[module._MT_TEACHING_SYNC_ENABLED] is True
    assert fake.session_state[module._MT_IMAGE_AUTOFIT_ENABLED] is True
    assert "#### Thiết lập ngày và tài liệu" in fake.labels


def test_select_all_and_clear_all_include_extended_controls(monkeypatch):
    state = {}
    monkeypatch.setattr(
        module,
        "st",
        SimpleNamespace(session_state=state),
    )

    module._set_all_standardization_options(False)

    assert state[module._MT_DRAFTING_ENABLED] is False
    assert state[module._MT_APPROVAL_ENABLED] is False
    assert state[module._MT_TEACHING_SYNC_ENABLED] is False
    assert state[module._MT_IMAGE_AUTOFIT_ENABLED] is False

    module._set_all_standardization_options(True)

    assert state[module._MT_DRAFTING_ENABLED] is True
    assert state[module._MT_APPROVAL_ENABLED] is True
    assert state[module._MT_TEACHING_SYNC_ENABLED] is True
    assert state[module._MT_IMAGE_AUTOFIT_ENABLED] is True


def test_final_panel_uses_original_expander_without_appending_controls():
    final_source = inspect.getsource(
        module._render_standardization_control_panel
    )
    original_source = inspect.getsource(
        module._mt_original_standardization_control_panel
    )

    assert "_mt_original_standardization_control_panel()" in final_source
    assert "_mt_original_standardization_control_panel_3c()" not in final_source
    assert (
        "_render_standardization_date_and_document_options()"
        in original_source
    )
    assert original_source.index(
        "_render_standardization_date_and_document_options()"
    ) < original_source.index(
        'key="standardization_control_panel_confirm"'
    )
